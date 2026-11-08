
from pathlib import Path
import hashlib
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "datasets/images/garden_image_provenance.csv"
OUTPUT = ROOT / "datasets/splits/garden_split_v1.csv"

df = pd.read_csv(MANIFEST)

def group_id(row):
    title = str(row["source_title"]).strip().lower()

    if "rma-urban roots" in title:
        return "series_rma_urban_roots"

    if title and title != "nan":
        return "source_" + hashlib.sha256(
            title.encode("utf-8")
        ).hexdigest()[:16]

    raise ValueError(
        f"Missing source_title for image: {row['file']}"
    )

df["group_id"] = df.apply(group_id, axis=1)

# Check that each file is unique.
if df["file"].duplicated().any():
    raise ValueError("Duplicate file paths in manifest")

# Check that source images and synthetic variants share a group.
source_groups = df.groupby("source_title")["group_id"].nunique()

assert source_groups.max() == 1, (
    "Images from the same source have different group IDs"
)

# Conserver RMA dans l'entraînement.
df["split"] = ""

groups = sorted(df["group_id"].unique())
for group in groups:
    if group == "series_rma_urban_roots":
        split = "train"
    else:
        # Attribution déterministe par groupe.
        digest = hashlib.sha256(group.encode()).hexdigest()
        bucket = int(digest[:8], 16) % 100
        split = (
            "train" if bucket < 70
            else "val" if bucket < 85
            else "test"
        )
    df.loc[df["group_id"] == group, "split"] = split

# Aucun groupe ne doit traverser les ensembles.
assert df.groupby("group_id")["split"].nunique().max() == 1

print(pd.crosstab(df["split"], df["label"]))

# Les trois classes doivent être représentées partout.
required = {"garden", "not_garden", "unusable"}
for split in ("train", "val", "test"):
    labels = set(df.loc[df["split"] == split, "label"])
    if labels != required:
        raise RuntimeError(
            f"Répartition invalide pour {split}: {labels}"
        )

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
df[["file", "label", "group_id", "split"]].to_csv(
    OUTPUT, index=False
)
print("Fichier créé :", OUTPUT)
