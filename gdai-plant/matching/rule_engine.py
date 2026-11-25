"""Versioned, extensible provisional matching rules."""
from dataclasses import dataclass
from matching.rules import horticultural, landscape, maintenance, preferences

@dataclass(frozen=True)
class Rule:
    id: str
    evaluate: object

RULES = tuple(Rule(i, f) for module in (horticultural, landscape, maintenance, preferences)
              for i, f in module.RULES)

def evaluate(g, p, config):
    reasons = {k: [] for k in ("incompatible","unknown","conditional","advisory","matched")}
    known = {r.id for r in RULES}
    enabled = config["enabled_rules"]
    if len(known) != len(RULES) or len(set(enabled)) != len(enabled) or not set(enabled) <= known:
        raise ValueError("Invalid rule registry/configuration")
    for rule in RULES:
        if rule.id in enabled:
            for kind, detail in rule.evaluate(g,p,config):
                reasons[kind].append(rule.id + ":" + detail)
    label = (0 if reasons["incompatible"] else None if reasons["unknown"] else
             1 if reasons["conditional"] else 3 if reasons["matched"] else 2)
    return label,reasons
