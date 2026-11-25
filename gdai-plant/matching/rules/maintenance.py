def size_advice(gkey,pkey):
    def check(g,p,c):
        a,b=g.get(gkey),p.get(pkey)
        if a is None or b is None: return [("advisory","unknown_"+pkey)]
        return [("advisory","review_size_management_"+pkey)] if a<b[1] else []
    return check

RULES=[("ENTR-001",size_advice("maximum_height_cm","height_cm")),
       ("ENTR-002",size_advice("maximum_spread_cm","spread_cm"))]
