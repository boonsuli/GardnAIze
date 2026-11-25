"""Preview horticultural evidence consolidation. No database writes."""

import json
import os
from collections import defaultdict

import psycopg
from psycopg.rows import dict_row


def main():
    dsn = os.environ.get("GDAI_PLANT_DSN")
    if not dsn:
        raise SystemExit("GDAI_PLANT_DSN is required")

    sql = """
        SELECT
            p.plant_id,
            p.scientific_name,
            p.quality_status,
            p.is_evergreen,
            e.attribute_name,
            e.value_as_reported,
            e.evidence_type,
            ds.source_name,
            psr.source_url
        FROM horticulture.plant_attribute_evidence e
        JOIN horticulture.plant p
          ON p.plant_id = e.plant_id
        JOIN horticulture.data_source ds
          ON ds.data_source_id = e.data_source_id
        JOIN horticulture.plant_source_record psr
          ON psr.plant_source_record_id = e.source_record_id
        WHERE p.scientific_name IN (
            'Geranium macrorrhizum',
            'Vinca minor'
        )
        ORDER BY p.scientific_name, e.attribute_name
    """

    with psycopg.connect(dsn) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql)
            rows = cur.fetchall()

    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["scientific_name"], row["attribute_name"])].append(row)

    report = {
        "mode": "DRY_RUN",
        "evidence_count": len(rows),
        "plant_count": len({r["plant_id"] for r in rows}),
        "candidates": [],
        "conflicts": [],
        "retained": [],
    }

    for (plant, attribute), entries in grouped.items():
        values = {
            json.dumps(r["value_as_reported"], sort_keys=True)
            for r in entries
        }

        if len(values) > 1:
            report["conflicts"].append({
                "plant": plant,
                "attribute": attribute,
                "values": sorted(values),
            })
            continue

        value = entries[0]["value_as_reported"]

        # Only a strictly defined, lossless mapping is proposed.
        if attribute == "foliage_persistence" and value == "EVERGREEN":
            report["candidates"].append({
                "plant": plant,
                "target": "horticulture.plant.is_evergreen",
                "value": True,
                "current_value": entries[0]["is_evergreen"],
                "status": "REQUIRES_REVIEW",
            })
        else:
            report["retained"].append({
                "plant": plant,
                "attribute": attribute,
                "value": value,
                "reason": "No approved canonical mapping",
            })

    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
