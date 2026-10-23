"""Create 600 synthetic plants for notebook smoke tests only; NOT botanical facts."""
from pathlib import Path
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
n = 600
types = rng.choice(["SHRUB", "TREE", "PERENNIAL", "GRASS"], n)
sun = rng.choice(["FULL_SUN", "PARTIAL_SHADE", "SHADE"], n)
soil = rng.choice(["WELL_DRAINED", "LOAM", "CLAY", "SAND"], n)
height = rng.integers(20, 450, n)
water = np.where((sun == "FULL_SUN") & (soil == "SAND"), "LOW",
                 np.where(soil == "CLAY", "HIGH", "MEDIUM"))
# Intentionally synthetic target relationship; supervised scores are NOT real evidence.
frame = pd.DataFrame({
    "plant_id": [f"SYN-{i:04d}" for i in range(n)],
    "scientific_name": [f"Synthetic species {i:04d}" for i in range(n)],
    "plant_type": types,
    "evergreen": rng.choice([True, False], n),
    "height_cm": height,
    "spread_cm": (height * rng.uniform(.35, 1.5, n)).astype(int),
    "hardiness_min_c": rng.choice([-25, -20, -15, -10, -5, 0], n),
    "sun_exposure": sun,
    "soil_type": soil,
    "water_need": water,
    "data_origin": "SYNTHETIC_DEMO"
})
dest = Path(__file__).resolve().parent / "plants_SYNTHETIC_DEMO.csv"
frame.to_csv(dest, index=False)
print(f"Wrote {len(frame)} synthetic records: {dest}")
