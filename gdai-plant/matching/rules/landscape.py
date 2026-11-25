"""Spatial suitability is distinct from biological incompatibility."""
from matching.rules.horticultural import membership

def restricted_space(g,p,c):
    category=p.get("category")
    if category is None: return [("unknown","plant_category")]
    h,w=g.get("maximum_height_cm"),g.get("maximum_spread_cm")
    if h is None or w is None: return [("unknown","available_space")]
    small=h<=c["small_space_height_cm"] or w<=c["small_space_spread_cm"]
    if not small: return []
    if category=="TREE": return [("conditional","tree_in_restricted_space")]
    if category in ("SHRUB","GRASS","PERENNIAL"):
        # Hedges are intentionally managed; no automatic size penalty.
        if category=="SHRUB" and g.get("planting_context")=="HEDGE": return []
        ph,pw=p.get("height_cm"),p.get("spread_cm")
        if ph is None or pw is None: return [("advisory","review_compactness")]
        if ph[0]>h or pw[0]>w: return [("conditional","prefer_compact_vegetation")]
    return []

def hedge(g,p,c):
    if g.get("planting_context")=="HEDGE" and p.get("category") in ("PERENNIAL","GRASS","GROUNDCOVER"):
        return [("conditional","prefer_hedge_vegetation")]
    return []

RULES=[("PAYS-001",restricted_space),
       ("PAYS-003",membership("planting_context","planting_context","conditional")),
       ("PAYS-004",hedge)]
