#!/usr/bin/env python3
import argparse
import csv
import json
from pathlib import Path

from import_plants import normalize, valid_horticultural_name


def read_names(path):
    path = Path(path)

    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError(f"{path}: expected JSON array")
        for row in data:
            if isinstance(row, dict):
                yield row.get("scientific_name", "")
            elif isinstance(row, str):
                yield row

    elif path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if "scientific_name" not in (reader.fieldnames or []):
                raise ValueError(f"{path}: missing scientific_name")
            for row in reader:
                yield row["scientific_name"]
    else:
        raise ValueError(f"Unsupported format: {path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", nargs="+", required=True)
    parser.add_argument("--out-dir", default="gdai-plant/data")
    args = parser.parse_args()

    names = {}
    rejected = 0

    for source in args.sources:
        for raw in read_names(source):
            name = str(raw or "").strip()
            if not valid_horticultural_name(name):
                rejected += 1
                continue
            names.setdefault(normalize(name), name)

    catalog = sorted(names.values(), key=str.casefold)

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    for target in (300, 3000):
        if len(catalog) < target:
            print(f"plants-{target}.json: NOT CREATED "
                  f"({len(catalog)}/{target} available)")
            continue

        # Stable subset, not a horticultural quality ranking.
        selected = catalog[:target]
        path = out / f"plants-{target}.json"
        path.write_text(
            json.dumps(
                [{"scientific_name": n} for n in selected],
                ensure_ascii=False,
                indent=2
            ) + "\n",
            encoding="utf-8"
        )
        print(f"Created {path}: {len(selected)} plants")

    print(f"Unique valid names: {len(catalog)}")
    print(f"Rejected records: {rejected}")


if __name__ == "__main__":
    main()
