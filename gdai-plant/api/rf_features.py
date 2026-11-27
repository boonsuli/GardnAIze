"""Shared feature encoding; no offline rules."""
GARDEN = ("sun_exposure", "soil_drainage", "water_availability",
          "minimum_winter_temperature_c", "maximum_height_cm", "maximum_spread_cm",
          "evergreen_preferred", "soil_texture", "soil_moisture_seasonality",
          "planting_context", "maintenance_preference")
PLANT = ("sun_exposure", "soil_drainage", "water_need", "hardiness_min_c",
         "height_cm", "spread_cm", "evergreen", "soil_type",
         "soil_moisture_tolerance", "planting_context", "category",
         "heat_tolerance", "drought_tolerance", "maintenance_level")


def features(row):
    result = {}
    for prefix, fields in (("garden_", GARDEN), ("plant_", PLANT)):
        for field in fields:
            key = prefix + field
            value = row.get(key)
            if value is None:
                result[key + ":missing"] = 1
            elif field in ("height_cm", "spread_cm"):
                result[key + ":min"], result[key + ":max"] = value
            elif isinstance(value, list):
                for item in value:
                    result[key + ":" + str(item)] = 1
            else:
                result[key] = value
    return result

