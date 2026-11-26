"""Stable bilingual advice identifiers; no external API calls."""
ADVICE = {
    "FROST_PROTECTION": ("Protéger la plante lors des épisodes de gel, selon sa rusticité et son mode de culture.", "Protect the plant during frost events according to its hardiness and growing conditions."),
    "SUPPLEMENTAL_WATERING": ("Prévoir un arrosage complémentaire adapté, en respectant les restrictions locales et sans saturer le sol.", "Provide suitable supplemental watering, respecting local restrictions and avoiding waterlogging."),
    "SOIL_AMENDMENT": ("Adapter le sol après vérification de sa texture et des besoins de la plante ; éviter les amendements systématiques.", "Adapt the soil after checking its texture and the plant's needs; avoid indiscriminate amendments."),
    "DRAINAGE_IMPROVEMENT": ("Améliorer le drainage après diagnostic du sol et vérification de la possibilité d'évacuer l'eau.", "Improve drainage after assessing the soil and confirming that excess water can safely drain."),
    "MULCHING": ("Pailler le sol pour limiter l'évaporation, sans couvrir le collet de la plante.", "Mulch to reduce evaporation, keeping mulch away from the plant crown."),
    "RAISED_BED": ("Prévoir un massif surélevé adapté au volume racinaire et au drainage nécessaire.", "Provide a raised bed suitable for root volume and drainage requirements."),
    "REGULAR_PRUNING": ("Tailler aux périodes adaptées à l'espèce, sans dépasser sa tolérance à la taille.", "Prune at species-appropriate times without exceeding its pruning tolerance."),
}
def render_advice(ids, language="FR"):
    if language not in ("FR", "EN"):
        raise ValueError("Unsupported advice language")
    return [{"advice_id": key, "text": ADVICE[key][language == "EN"]}
            for key in sorted(set(ids))]
