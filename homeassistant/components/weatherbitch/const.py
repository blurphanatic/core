"""Constants for the Met Office integration."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.components.weather import (
    ATTR_CONDITION_CLEAR_NIGHT,
    ATTR_CONDITION_CLOUDY,
    ATTR_CONDITION_FOG,
    ATTR_CONDITION_HAIL,
    ATTR_CONDITION_LIGHTNING,
    ATTR_CONDITION_PARTLYCLOUDY,
    ATTR_CONDITION_RAINY,
    ATTR_CONDITION_SNOWY,
    ATTR_CONDITION_SUNNY,
)

DOMAIN = "weatherbitch" # Retaining "weatherbitch" as per user override

CONF_API_KEY = "api_key"

UPDATE_INTERVAL = timedelta(minutes=15)

CONF_TIMESTEPS = "timesteps"
TIMESTEP_OPTIONS = ["hourly", "three-hourly", "daily"]

CONF_UPDATE_INTERVAL = "update_interval"
MIN_UPDATE_INTERVAL = timedelta(minutes=15)
MAX_UPDATE_INTERVAL = timedelta(hours=6)

API_CALL_COUNTER_KEY = f"{DOMAIN}_api_call_counter"

DEFAULT_TIMESTEPS = "hourly"

# Base URL for the Met Office DataHub point forecast API (CORRECTED BASE_URL)
BASE_URL = "https://data.hub.api.metoffice.gov.uk/sitespecific/v0"

# Mandatory data source parameter for the point forecast API (ADDED)
DATA_SOURCE = "BD1"

METOFFICE_WEATHER_CODE_MAP: dict[int, str] = {
    0: ATTR_CONDITION_CLEAR_NIGHT,
    1: ATTR_CONDITION_SUNNY,
    2: ATTR_CONDITION_PARTLYCLOUDY,
    3: ATTR_CONDITION_PARTLYCLOUDY,
    4: ATTR_CONDITION_SUNNY, # This code is often unused or deprecated, mapping to sunny
    5: ATTR_CONDITION_FOG,
    6: ATTR_CONDITION_FOG,
    7: ATTR_CONDITION_CLOUDY,
    8: ATTR_CONDITION_CLOUDY,
    9: ATTR_CONDITION_RAINY,
    10: ATTR_CONDITION_RAINY,
    11: ATTR_CONDITION_RAINY,
    12: ATTR_CONDITION_RAINY,
    13: ATTR_CONDITION_RAINY,
    14: ATTR_CONDITION_RAINY,
    15: ATTR_CONDITION_RAINY,
    16: ATTR_CONDITION_SNOWY,
    17: ATTR_CONDITION_SNOWY,
    18: ATTR_CONDITION_SNOWY,
    19: ATTR_CONDITION_HAIL,
    20: ATTR_CONDITION_HAIL,
    21: ATTR_CONDITION_HAIL,
    22: ATTR_CONDITION_SNOWY,
    23: ATTR_CONDITION_SNOWY,
    24: ATTR_CONDITION_SNOWY,
    25: ATTR_CONDITION_SNOWY,
    26: ATTR_CONDITION_SNOWY,
    27: ATTR_CONDITION_SNOWY,
    28: ATTR_CONDITION_LIGHTNING, # Mapped to generic lightning as per directive
    29: ATTR_CONDITION_LIGHTNING, # Mapped to generic lightning as per directive
    30: ATTR_CONDITION_LIGHTNING, # Mapped to generic lightning as per directive
}
