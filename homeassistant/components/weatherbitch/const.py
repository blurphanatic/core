"""Constants for the Met Office integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "metoffice"

CONF_API_KEY = "api_key"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"

UPDATE_INTERVAL = timedelta(minutes=15)
DEFAULT_TIMESTEPS = "hourly"

METOFFICE_WEATHER_CODE_MAP: dict[int, str] = {
    0: "clear-night",
    1: "sunny",
    2: "partlycloudy",
    3: "partlycloudy",
    4: "sunny",
    5: "fog",
    6: "fog",
    7: "cloudy",
    8: "cloudy",
    9: "rainy",
    10: "rainy",
    11: "rainy",
    12: "rainy",
    13: "rainy",
    14: "rainy",
    15: "rainy",
    16: "snowy",
    17: "snowy",
    18: "snowy",
    19: "hail",
    20: "hail",
    21: "hail",
    22: "snowy",
    23: "snowy",
    24: "snowy",
    25: "snowy",
    26: "snowy",
    27: "snowy",
    28: "lightning",
    29: "lightning",
    30: "lightning",
}
