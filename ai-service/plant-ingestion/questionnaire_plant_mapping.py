"""Canonical questionnaire-to-plant attributes, not inferred horticultural values."""
QUESTION_MAPPING = {
 "exposure": {"plant_fields":["plant_sun_exposure"],"rule":"compatible exposure"},
 "soil": {"plant_fields":["plant_soil_type","minimum_soil_ph","maximum_soil_ph"],"rule":"compatible soil and pH when known"},
 "water": {"plant_fields":["water_requirement"],"rule":"requirement <= available water"},
 "maintenance": {"plant_fields":["maintenance_level","pruning_requirement"],"rule":"maintenance fits preference"},
 "evergreen": {"plant_fields":["is_evergreen"],"rule":"match preferred persistence"},
 "flower_color": {"plant_fields":["plant_color_assignment"],"rule":"FLOWER color preference"},
 "height_max": {"plant_fields":["maximum_height_cm"],"rule":"mature height fits limit"},
 "privacy": {"plant_fields":["plant_use_assignment","maximum_height_cm","maximum_spread_cm"],"rule":"screening use plus dimensions"},
 "budget": {"plant_fields":["plant_merchant_offer.price_amount"],"rule":"available offer total fits budget"},
 "climate": {"plant_fields":["minimum_hardiness_c","maximum_temperature_c","is_heat_tolerant"],"rule":"climate suitability"}
}
