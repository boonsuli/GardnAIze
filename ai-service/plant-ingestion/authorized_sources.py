"""Explicitly approved local CSV adapters. No crawling or merchant API assumptions."""
import csv
from pathlib import Path

MERCHANTS = {
 "truffaut":"https://www.truffaut.com",
 "leroymerlin":"https://www.leroymerlin.fr",
 "vegetalo":"https://www.vegetalo.com",
 "bakker":"https://www.bakker.com",
 "gammvert":"https://www.gammvert.fr",
 "rouepepinieres":"https://www.rouepepinieres.com",
}
REQUIRED = {"scientific_name","external_offer_id","price_amount","currency"}

def read_merchant_export(csv_path, manifest, column_map):
    """Manifest requires documented permission, not merely a public product page."""
    if not (manifest.get("commercial_reuse_allowed") and manifest.get("automated_access_allowed")):
        raise PermissionError("Merchant export not approved")
    if not (manifest.get("license") or manifest.get("written_permission")):
        raise PermissionError("Documented reuse permission required")
    if manifest.get("name") not in MERCHANTS:
        raise ValueError("Unknown merchant")
    if not REQUIRED.issubset(column_map):
        raise ValueError("Missing canonical columns")
    with Path(csv_path).open(newline="",encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            item={k:(row.get(source) or "").strip() for k,source in column_map.items()}
            if not item["scientific_name"] or not item["external_offer_id"]:
                continue
            if item["currency"]!="EUR":
                raise ValueError("Non-EUR currency requires explicit conversion")
            amount=float(item["price_amount"].replace(",","."))
            if amount<0:
                raise ValueError("Negative price")
            item["price_amount"]=amount
            item["source"]=manifest["name"]
            yield item
