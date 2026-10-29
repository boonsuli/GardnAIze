#!/usr/bin/env python3
"""Download a small auditable garden-scene dataset from Wikimedia Commons.

Requires: pip install requests pillow
This script never commits photos. Inspect labels, provenance and licenses manually.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import random
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
from PIL import Image, ImageEnhance, ImageFilter, UnidentifiedImageError

API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "GardnAIzeEducationalDataset/0.1 (research; Wikimedia Commons API)"
QUERIES = {
    "garden": ["residential backyard garden", "private garden lawn", "small urban garden"],
    "not_garden": ["city street buildings", "kitchen interior", "automobile parked"],
}
# Explicitly exclude restrictive and share-alike licenses from the automatic subset.
# Other restrictions and attribution obligations still require human review.
ALLOWED = {"CC0", "CC BY 4.0", "CC BY 3.0", "Public domain"}
FIELDS = ["label", "file", "commons_page", "original_url", "author_html",
          "license", "license_url", "retrieved_at", "sha256", "source_title", "review_status"]


def value(metadata, key):
    return metadata.get(key, {}).get("value", "")


def candidates(session, query, limit):
    params = {
        "action": "query", "format": "json", "formatversion": "2",
        "generator": "search", "gsrsearch": 'filetype:bitmap ' + query,
        "gsrnamespace": 6, "gsrlimit": min(max(limit, 1), 50),
        "prop": "imageinfo", "iiprop": "url|extmetadata", "iiurlwidth": 1024,
    }
    response = session.get(API, params=params, timeout=35)
    response.raise_for_status()
    return response.json().get("query", {}).get("pages", [])


def retrieve(session, image_url):
    response = session.get(image_url, timeout=40, stream=True)
    response.raise_for_status()
    data = bytearray()
    for chunk in response.iter_content(64 * 1024):
        data.extend(chunk)
        if len(data) > 8 * 1024 * 1024:
            raise ValueError("Image exceeds 8 MiB")
    with Image.open(io.BytesIO(data)) as image:
        image.load()
        if image.width < 350 or image.height < 250:
            raise ValueError("Image too small")
        if image.width * image.height > 30_000_000:
            raise ValueError("Image too large")
        image = image.convert("RGB")
        image.thumbnail((1024, 1024))
        output = io.BytesIO()
        image.save(output, format="JPEG", quality=85)
    return output.getvalue()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-class", type=int, default=30)
    parser.add_argument("--test-fraction", type=float, default=0.2)
    parser.add_argument("--output", type=Path, default=Path("datasets/images"))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if not (1 <= args.per_class <= 100 and 0 < args.test_fraction < 0.5):
        parser.error("--per-class must be 1..100 and --test-fraction between 0 and 0.5")
    random.seed(args.seed)
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    records = []
    seen = set()
    now = datetime.now(timezone.utc).isoformat()

    for label, searches in QUERIES.items():
        pool = []
        for term in searches:
            try:
                pool.extend(candidates(session, term, args.per_class * 2))
            except (requests.RequestException, ValueError) as exc:
                print(f"Search failed ({term}): {exc}")
            time.sleep(0.3)
        random.shuffle(pool)
        count = 0
        for page in pool:
            if count >= args.per_class:
                break
            infos = page.get("imageinfo") or []
            if not infos:
                continue
            info = infos[0]
            meta = info.get("extmetadata", {})
            license_name = value(meta, "LicenseShortName")
            if license_name not in ALLOWED:
                continue
            url = info.get("thumburl") or info.get("url", "")
            if not url.startswith("https://"):
                continue
            if not urlparse(url).hostname.endswith("wikimedia.org"):
                continue
            title = page.get("title", "")
            if title in seen:
                continue
            try:
                photo = retrieve(session, url)
                digest = hashlib.sha256(photo).hexdigest()
                if digest in seen:
                    continue
                # Keep Commons category-derived labels provisional: review every image.
                split = "garden_test" if count % 5 == 0 else "garden_validation"
                folder = args.output / split / label
                folder.mkdir(parents=True, exist_ok=True)
                filename = f"{label}_{count + 1:04d}_{digest[:10]}.jpg"
                (folder / filename).write_bytes(photo)
                seen.update((title, digest))
                records.append({
                    "label": label, "file": str(folder / filename),
                    "commons_page": info.get("descriptionurl", ""),
                    "original_url": info.get("url", ""), "author_html": value(meta, "Artist"),
                    "license": license_name, "license_url": value(meta, "LicenseUrl"),
                    "retrieved_at": now, "sha256": digest, "source_title": title,
                    "review_status": "pending_manual_review",
                })
                count += 1
                print(f"{label}: {count}/{args.per_class}")
            except (requests.RequestException, ValueError, OSError, UnidentifiedImageError) as exc:
                print(f"Skipping {title}: {exc}")
            time.sleep(0.2)
        print(f"{label}: downloaded {count} candidate images")

    # Synthetic unusable variants are generated ONLY from training/validation
    # garden images. They are NOT copied into the test split.
    originals = [r for r in records if r["label"] == "garden" and "garden_validation" in r["file"]]
    for index, item in enumerate(originals[:args.per_class]):
        with Image.open(item["file"]) as source:
            image = source.convert("RGB")
            if index % 2:
                image = ImageEnhance.Brightness(image).enhance(0.06)
            else:
                image = image.filter(ImageFilter.GaussianBlur(radius=18))
            dest = args.output / "garden_validation" / "unusable"
            dest.mkdir(parents=True, exist_ok=True)
            target = dest / f"unusable_{index + 1:04d}.jpg"
            image.save(target, quality=82)
            records.append({
                **item, "label": "unusable", "file": str(target),
                "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                "review_status": "synthetic_derived_from_training_image",
            })
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = args.output / "garden_image_provenance.csv"
    with manifest.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(records)
    print(f"Saved {len(records)} candidate images; manifest: {manifest}")
    print("IMPORTANT: visually verify labels, rights and train/test leakage before training.")
    print("Unusable test images must be independently collected or derived from test-only source photos.")


if __name__ == "__main__":
    main()
