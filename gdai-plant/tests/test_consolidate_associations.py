"""Isolated unit tests for consolidate_associations.run; no PostgreSQL writes."""
import importlib.util
import io
import sys
import types
from contextlib import redirect_stdout
from pathlib import Path
from unittest import TestCase, main
from unittest.mock import patch

# Use a minimal psycopg stub only if the test runner lacks the dependency.
try:
    import psycopg
except ImportError:
    sys.modules['psycopg'] = types.ModuleType('psycopg')
    sys.modules['psycopg'].connect = lambda *_: None
    rows_module = types.ModuleType('psycopg.rows')
    rows_module.dict_row = object()
    sys.modules['psycopg.rows'] = rows_module

MODULE = Path(__file__).resolve().parents[1] / 'enrichment' / 'consolidate_associations.py'
spec = importlib.util.spec_from_file_location('consolidate_associations', MODULE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def evidence(plant_id, name, attr, values, rights=True, evidence_id=1):
    return dict(plant_id=plant_id, scientific_name=name, attribute_name=attr,
                value_as_reported=values, commercial_reuse_allowed=rights,
                evidence_type='OBSERVED', source_name='TEST_LICENSED',
                evidence_id=evidence_id, source_url='https://example.org/test')


class FakeCursor:
    def __init__(self, db):
        self.db = db
        self.rows = []
        self.one = None

    def __enter__(self): return self
    def __exit__(self, *args): return False

    def execute(self, sql, params=None):
        normalized = ' '.join(sql.split())
        self.db.queries.append((normalized, params))
        if 'FROM horticulture.plant_attribute_evidence e' in normalized:
            self.rows = self.db.evidence
        elif 'FROM horticulture.sun_exposure WHERE code=' in normalized:
            self.one = {'id': {'FULL_SUN': 1, 'PARTIAL_SHADE': 2, 'FULL_SHADE': 3}.get(params[0])} if params[0] in ('FULL_SUN','PARTIAL_SHADE','FULL_SHADE') else None
        elif 'FROM horticulture.plant_use WHERE code=' in normalized:
            self.one = {'id': {'GROUND_COVER': 5}.get(params[0])} if params[0] == 'GROUND_COVER' else None
        elif 'SELECT 1 FROM horticulture.plant_sun_exposure' in normalized:
            self.one = (1,) if ('sun', *params) in self.db.associations else None
        elif 'SELECT 1 FROM horticulture.plant_use_assignment' in normalized:
            self.one = (1,) if ('use', *params) in self.db.associations else None
        elif normalized.startswith('INSERT INTO horticulture.plant_sun_exposure'):
            self.db.associations.add(('sun', *params))
        elif normalized.startswith('INSERT INTO horticulture.plant_use_assignment'):
            self.db.associations.add(('use', *params))
        else:
            raise AssertionError(f'Unexpected SQL: {normalized}')

    def fetchall(self): return self.rows
    def fetchone(self): return self.one


class FakeTransaction:
    def __init__(self, db): self.db = db
    def __enter__(self):
        self.snapshot = self.db.associations.copy()
        return self
    def __exit__(self, typ, value, tb):
        if typ is not None:
            self.db.associations = self.snapshot
        return False


class FakeConnection:
    def __init__(self, db): self.db = db
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def transaction(self): return FakeTransaction(self.db)
    def cursor(self, **kwargs): return FakeCursor(self.db)


class FakeDB:
    def __init__(self, rows):
        self.evidence = rows
        self.associations = set()
        self.queries = []
    def connect(self, _dsn): return FakeConnection(self)


class ConsolidationTests(TestCase):
    def execute(self, db, apply=False, approved=False):
        out = io.StringIO()
        with patch.object(mod.psycopg, 'connect', db.connect), redirect_stdout(out):
            mod.run('fake-dsn', apply=apply, approved=approved)
        return out.getvalue()

    def test_dry_run_plans_eight_without_writing(self):
        db = FakeDB([
            evidence(1, 'Geranium macrorrhizum', 'sun_exposure', ['FULL_SUN','PARTIAL_SHADE','FULL_SHADE']),
            evidence(1, 'Geranium macrorrhizum', 'garden_uses', ['GROUND_COVER','FLOWER_BORDERS'], evidence_id=2),
            evidence(2, 'Vinca minor', 'sun_exposure', ['FULL_SUN','PARTIAL_SHADE','FULL_SHADE'], evidence_id=3),
            evidence(2, 'Vinca minor', 'garden_uses', ['GROUND_COVER','UNDERPLANTING'], evidence_id=4),
        ])
        out = self.execute(db)
        self.assertEqual(out.count('PLAN '), 8)
        self.assertEqual(out.count('SKIP unmapped:'), 2)
        self.assertFalse(db.associations)
        self.assertFalse(any(q.startswith('INSERT') for q, _ in db.queries))

    def test_apply_is_idempotent(self):
        db = FakeDB([evidence(2, 'Vinca minor', 'sun_exposure', ['FULL_SUN','PARTIAL_SHADE','FULL_SHADE'])])
        self.execute(db, apply=True, approved=True)
        self.assertEqual(len(db.associations), 3)
        self.execute(db, apply=True, approved=True)
        self.assertEqual(len(db.associations), 3)

    def test_rights_unknown_skips(self):
        db = FakeDB([evidence(2, 'Vinca minor', 'garden_uses', ['GROUND_COVER'], rights=None)])
        out = self.execute(db, apply=True, approved=True)
        self.assertIn('SOURCE_RIGHTS_NOT_CONFIRMED', out)
        self.assertFalse(db.associations)

    def test_apply_requires_approval(self):
        with self.assertRaises(ValueError):
            mod.run('fake-dsn', apply=True, approved=False)

    def test_conflicting_values_abort(self):
        db = FakeDB([
            evidence(1, 'Geranium macrorrhizum', 'sun_exposure', ['FULL_SUN'], evidence_id=1),
            evidence(1, 'Geranium macrorrhizum', 'sun_exposure', ['FULL_SHADE'], evidence_id=2),
        ])
        with patch.object(mod.psycopg, 'connect', db.connect), self.assertRaises(ValueError):
            mod.run('fake-dsn', apply=True, approved=True)
        self.assertFalse(db.associations)

    def test_unexpected_sql_failure_rolls_back_fake_transaction(self):
        db = FakeDB([evidence(1, 'Geranium macrorrhizum', 'sun_exposure', ['FULL_SUN','PARTIAL_SHADE'])])
        original = FakeCursor.execute
        def fail_second_insert(cursor, sql, params=None):
            if sql.lstrip().startswith('INSERT INTO horticulture.plant_sun_exposure') and params == (1, 2):
                raise RuntimeError('Simulated database failure')
            return original(cursor, sql, params)
        with patch.object(mod.psycopg, 'connect', db.connect), patch.object(FakeCursor, 'execute', fail_second_insert), self.assertRaises(RuntimeError):
            mod.run('fake-dsn', apply=True, approved=True)
        self.assertFalse(db.associations)


if __name__ == '__main__': main()
