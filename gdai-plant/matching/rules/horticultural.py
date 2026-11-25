"""Biological constraints; missing evidence is not a negative label."""
def membership(gkey,pkey,severity):
    def check(g,p,c):
        a,b=g.get(gkey),p.get(pkey)
        if a is None or b is None:
            return [("unknown",pkey)]
        return [(severity,pkey)] if a not in b else []
    return check

def frost(g,p,c):
    a,b=g.get("minimum_winter_temperature_c"),p.get("hardiness_min_c")
    if a is None or b is None: return [("unknown","hardiness_min_c")]
    if a < b: return [("incompatible","hardiness_min_c")]
    return [("conditional","frost_margin")] if a-b <= c["frost_margin_c"] else []

def water(g,p,c):
    a,b=g.get("water_availability"),p.get("water_need")
    if a is None or b is None: return [("unknown","water_need")]
    levels={"LOW":0,"MEDIUM":1,"HIGH":2}
    gap=levels[b]-levels[a]
    return [("incompatible" if gap>=2 else "conditional","water_need")] if gap>0 else []

RULES=[
 ("HORT-001",membership("sun_exposure","sun_exposure","incompatible")),
 ("HORT-002",frost),
 ("HORT-003",membership("soil_drainage","soil_drainage","incompatible")),
 ("HORT-004",water),
 ("HORT-005",membership("soil_texture","soil_type","conditional")),
 ("HORT-006",membership("soil_moisture_seasonality","soil_moisture_tolerance","conditional"))]
