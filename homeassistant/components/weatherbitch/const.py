"""Met Office constants."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "weatherbitch"

CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"

BASE_URL = "https://data-proxy.api.metoffice.gov.uk/val/wxfcs"

DEFAULT_SCAN_INTERVAL = timedelta(minutes=15)

VISIBILITY_MAP: dict[str, str] = {
    "VP": "Very Poor (<1 km)",
    "PO": "Poor (1-4 km)",
    "MO": "Moderate (4-10 km)",
    "GO": "Good (10-20 km)",
    "VG": "Very Good (20-40 km)",
    "EX": "Excellent (>40 km)",
}

W_CODE_CONDITION_MAP: dict[int, str] = {
    0: "clear-night",
    1: "sunny",
    2: "partlycloudy",
    3: "partlycloudy",
    5: "fog",
    6: "fog",
    7: "cloudy",
    8: "cloudy",
    9: "pouring",
    10: "pouring",
    11: "rainy",
    12: "rainy",
    13: "pouring",
    14: "pouring",
    15: "pouring",
    16: "snowy-rainy",
    17: "snowy-rainy",
    18: "snowy-rainy",
    19: "hail",
    20: "hail",
    21: "hail",
    22: "snowy",
    23: "snowy",
    24: "snowy",
    25: "snowy",
    26: "snowy",
    27: "snowy",
    28: "lightning-rainy",
    29: "lightning-rainy",
    30: "lightning",
}
