"""PostgreSQL integration tests for plant associations."""

import os
import unittest

import psycopg


class PostgresAssociationIT(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        dsn = os.getenv("GDAI_PLANT_DSN")
        if not dsn:
            raise unittest.SkipTest("GDAI_PLANT_DSN not configured")
        cls.dsn = dsn

    def setUp(self):
        self.conn = psycopg.connect(self.dsn)
        self.conn.autocommit = False
        self.cur = self.conn.cursor()

        self.cur.execute("""
            SELECT plant_id
            FROM horticulture.plant
            WHERE scientific_name = 'Vinca minor'
        """)
        row = self.cur.fetchone()
        if row is None:
            self.conn.close()
            self.skipTest("Vinca minor not found")

        self.plant_id = row[0]

    def tearDown(self):
        if hasattr(self, "conn") and not self.conn.closed:
            self.conn.rollback()
            self.conn.close()

    def test_idempotent_associations(self):
        self.cur.execute("""
            SELECT sun_exposure_id
            FROM horticulture.sun_exposure
            WHERE code = 'PARTIAL_SHADE'
        """)
        sun_id = self.cur.fetchone()[0]

        sql = """
            INSERT INTO horticulture.plant_sun_exposure
                (plant_id, sun_exposure_id, suitability)
            VALUES (%s, %s, 'SUITABLE')
            ON CONFLICT (plant_id, sun_exposure_id)
            DO NOTHING
        """

        self.cur.execute(sql, (self.plant_id, sun_id))
        self.cur.execute(sql, (self.plant_id, sun_id))

        self.cur.execute("""
            SELECT COUNT(*)
            FROM horticulture.plant_sun_exposure
            WHERE plant_id = %s AND sun_exposure_id = %s
        """, (self.plant_id, sun_id))

        self.assertEqual(self.cur.fetchone()[0], 1)

    def test_rollback_after_failure(self):
        self.cur.execute("""
            SELECT plant_use_id
            FROM horticulture.plant_use
            WHERE code = 'GROUND_COVER'
        """)
        use_id = self.cur.fetchone()[0]

        self.cur.execute("""
            INSERT INTO horticulture.plant_use_assignment
                (plant_id, plant_use_id)
            VALUES (%s, %s)
            ON CONFLICT (plant_id, plant_use_id)
            DO NOTHING
        """, (self.plant_id, use_id))

        self.conn.rollback()

        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*)
                FROM horticulture.plant_use_assignment
                WHERE plant_id = %s AND plant_use_id = %s
            """, (self.plant_id, use_id))

            self.assertEqual(cur.fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
