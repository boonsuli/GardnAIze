"""Normalize FRONT answers without inventing environmental facts or consent."""
ENUMS = {
    "exposure": ("sun_exposure", {"FULL_SUN":"FULL_SUN","PARTIAL_SHADE":"PARTIAL_SHADE","SHADE":"FULL_SHADE"}),
    "soilType": ("soil_texture", {"SANDY":"SAND","CLAY":"CLAY","LOAMY":"SILT"}),
    "waterAvailability": ("water_availability", {"LOW":"LOW","MODERATE":"MEDIUM","HIGH":"HIGH"}),
    "maintenancePreference": ("maintenance_preference", {"LOW":"LOW","MODERATE":"MEDIUM","HIGH":"HIGH"}),
    "desiredHeight": ("desired_height", {"LOW":"LOW","MEDIUM":"MEDIUM","TALL":"TALL"}),
    "matureSpread": ("mature_spread_preference", {"UNDER_1M":"UNDER_1M","FROM_1_TO_2M":"FROM_1_TO_2M","FROM_2_TO_4M":"FROM_2_TO_4M","OVER_4M":"OVER_4M"}),
    "rootSpace": ("root_space", {v:v for v in ("VERY_LIMITED","LIMITED","MODERATE","UNRESTRICTED")}),
    "budget": ("budget", {v:v for v in ("LOW","MEDIUM","HIGH")}),
    "gardenStyle": ("garden_style", {v:v for v in ("CONTEMPORARY","NATURAL","MEDITERRANEAN")}),
    "preferredColors": ("preferred_color", {v:v for v in ("WHITE","PINK","PURPLE","YELLOW")}),
}
def map_questionnaire(answers):
    profile = {}
    for key, (target, values) in ENUMS.items():
        value = answers.get(key)
        if isinstance(value, str) and value in values:
            profile[target] = values[value]
    for key, target in (("evergreenPreferred","evergreen_preferred"),("privacyScreeningRequired","privacy_screening_required")):
        value = answers.get(key)
        if value is True or value == "YES":
            profile[target] = True
        elif value is False or value == "NO":
            profile[target] = False
    # Preferences are not measured dimensions. No implicit action acceptance.
    return profile
