"""Offline dataset audit. Never imported by recommendation serving."""
import argparse
import json
import math
from collections import Counter
from pathlib import Path


def audit(document, profile):
    """Report violations without mutating or silently correcting scenarios."""
    if profile["schema_version"] != 1:
        raise ValueError("Unsupported profile schema")
    rows = document["scenarios"]
    if not isinstance(rows, list):
        raise ValueError("scenarios must be a list")
    counts = Counter(row["id"] for row in rows)
    issues = []
    for row in rows:
        ident = row["id"]
        def flag(field, code):
            issues.append({"id": ident, "field": field, "code": code,
                           "value": row.get(field)})
        if counts[ident] != 1:
            flag("id", "DUPLICATE_ID")
        for field in profile.get("required_fields", []):
            if row.get(field) is None or row.get(field) == "":
                flag(field, "MISSING")
        for field, expected in profile.get("required_values", {}).items():
            if row.get(field) != expected:
                flag(field, "OUT_OF_SCOPE")
        for field, allowed in profile.get("allowed_values", {}).items():
            if row.get(field) not in allowed:
                flag(field, "OUT_OF_SCOPE")
        for field, bounds in profile.get("numeric_ranges", {}).items():
            value = row.get(field)
            if (isinstance(value, bool) or not isinstance(value, (int, float))
                    or not math.isfinite(value)):
                flag(field, "INVALID_NUMBER")
                continue
            lo, hi = bounds.get("min"), bounds.get("max")
            if ((lo is not None and value < lo)
                    or (hi is not None and value > hi)):
                flag(field, "OUT_OF_RANGE")
    flagged = {issue["id"] for issue in issues}
    return {"profile_id": profile["profile_id"], "total": len(rows),
            "flagged": sum(row["id"] in flagged for row in rows),
            "issues": issues, "target_count_met": len(rows) == profile["target_gardens"],
            "climate_distribution": dict(Counter(row.get("climate_zone") for row in rows))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = audit(json.loads(args.input.read_text(encoding="utf-8")),
                   json.loads(args.profile.read_text(encoding="utf-8")))
    with args.out.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    print(f"{report['flagged']}/{report['total']} scenarios require review")


if __name__ == "__main__":
    main()
