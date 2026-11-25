def evergreen(g,p,c):
    if g.get("evergreen_preferred") is not True: return []
    v=p.get("evergreen")
    return [("unknown","evergreen")] if v is None else [("matched","evergreen")] if v else [("conditional","evergreen_preference")]

RULES=[("PREF-001",evergreen)]
