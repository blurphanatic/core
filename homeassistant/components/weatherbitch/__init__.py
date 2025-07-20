"""The Met Office integration."""

# pylint: disable=hass-enforce-class-module

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import ApiError, MetOfficeApiClient
from .const import (
    API_CALL_COUNTER_KEY,
    CONF_API_KEY,
    CONF_TIMESTEPS,
    CONF_UPDATE_INTERVAL,
    DOMAIN,
    METOFFICE_WEATHER_CODE_MAP,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.WEATHER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Met Office entry."""
    api_key = entry.data[CONF_API_KEY]
    latitude = entry.data[CONF_LATITUDE]
    longitude = entry.data[CONF_LONGITUDE]
    timesteps = entry.data[CONF_TIMESTEPS]
    update_interval_minutes = entry.data[CONF_UPDATE_INTERVAL]
    update_interval_td = timedelta(minutes=update_interval_minutes)

    client = MetOfficeApiClient(hass, api_key)
    coordinator = MetOfficeDataUpdateCoordinator(
        hass, client, latitude, longitude, timesteps, update_interval_td, entry
    )

    hass.data.setdefault(DOMAIN, {})
    if API_CALL_COUNTER_KEY not in hass.data[DOMAIN]:
        hass.data[DOMAIN][API_CALL_COUNTER_KEY] = {
            "count": 0,
            "last_reset_date": datetime.now(UTC).date(),
        }

    hass.data[DOMAIN][entry.entry_id] = coordinator
    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


def get_device_info(latitude: float, longitude: float, name: str) -> DeviceInfo:
    """Return device registry information."""
    return DeviceInfo(
        entry_type=dr.DeviceEntryType.SERVICE,
        identifiers={(DOMAIN, f"{latitude},{longitude}")},
        manufacturer="Met Office",
        name=f"Met Office {name}",
    )


class MetOfficeDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to fetch data from the Met Office API."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: MetOfficeApiClient,
        latitude: float,
        longitude: float,
        timesteps: str,
        update_interval_td: timedelta,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance.
            client: API client used to retrieve forecasts.
            latitude: Latitude of forecast location.
            longitude: Longitude of forecast location.
            timesteps: Forecast frequency (hourly, three-hourly, daily).
            update_interval_td: Update interval for coordinator.
            config_entry: Config entry associated with this coordinator.
        """
        self.client = client
        self.latitude = latitude
        self.longitude = longitude
        self.timesteps = timesteps
        self.config_entry: ConfigEntry = config_entry
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval_td)
        self.data: dict[str, Any] = {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch latest data from Met Office."""
        try:
            # Use self.timesteps for the API call
            data = await self.client.get_point_forecast(
                self.latitude, self.longitude, self.timesteps
            )

            # --- API Call Counter Logic (Keep this, it was correct) ---
            api_counter = self.hass.data[DOMAIN][API_CALL_COUNTER_KEY]
            current_date = datetime.now(UTC).date()
            if current_date != api_counter["last_reset_date"]:
                api_counter["count"] = 0
                api_counter["last_reset_date"] = current_date
            api_counter["count"] += 1
            _LOGGER.info(
                "Met Office API call successful for %s. Total calls today: %d",
                self.config_entry.title,
                api_counter["count"],
            )
            # --- End API Call Counter Logic ---

        except ApiError as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err

        # --- API RESPONSE PARSING AND FORECAST CONVERSION ---
        features = data.get("features")
        if not isinstance(features, list) or not features:
            _LOGGER.warning(
                "API response 'features' list missing or empty: %s", features
            )
            raise UpdateFailed("Missing features in API response")

        properties = features[0].get("properties")
        if not isinstance(properties, dict):
            _LOGGER.warning(
                "API response 'properties' missing or not a dict: %s", properties
            )
            raise UpdateFailed("Missing properties in API response")

        time_series = properties.get("timeSeries")
        if not isinstance(time_series, list) or not time_series:
            _LOGGER.warning(
                "API response 'timeSeries' list missing or empty: %s", time_series
            )
            raise UpdateFailed("Missing timeSeries in API response")

        raw_ts = time_series
        processed: list[dict[str, Any]] = []
        for item in raw_ts:
            new = item.copy()
            if (v := new.get("mslp")) is not None:
                new["mslp_hpa"] = v / 100.0

            if "feelsLikeTemp" in new and "feelsLikeTemperature" not in new:
                new["feelsLikeTemperature"] = new["feelsLikeTemp"]

            dt = dt_util.parse_datetime(new.get("time"))
            new["datetime"] = dt or new.get("time")
            processed.append(new)

        now = dt_util.utcnow()
        future = [
            x
            for x in processed
            if isinstance(x.get("datetime"), datetime) and x["datetime"] > now
        ]
        forecast_list = future if future else processed

        ha_forecasts: list[dict[str, Any]] = [
            {
                "datetime": x.get("datetime"),
                "condition": METOFFICE_WEATHER_CODE_MAP.get(
                    x.get("significantWeatherCode"), "unknown"
                ),
                "temperature": x.get("screenTemperature"),
                "temperature_min": x.get("minScreenAirTemp"),
                "temperature_max": x.get("maxScreenAirTemp"),
                "feels_like": x.get("feelsLikeTemperature"),
                "dew_point": x.get("screenDewPointTemperature"),
                "humidity": x.get("screenRelativeHumidity"),
                "pressure": x.get("mslp_hpa"),
                "visibility": x.get("visibility"),
                "uv_index": x.get("uvIndex"),
                "wind_speed": x.get("windSpeed10m"),
                "wind_bearing": x.get("windDirectionFrom10m"),
                "wind_gust": x.get("windGustSpeed10m") or x.get("max10mWindGust"),
                "precipitation": x.get("precipitationRate"),
                "precipitation_amount": x.get("totalPrecipAmount"),
                "snow_amount": x.get("totalSnowAmount"),
                "precipitation_probability": x.get("probOfPrecipitation"),
                "weather_code": x.get("significantWeatherCode"),
                "raw": x,
            }
            for x in forecast_list
        ]

        current = ha_forecasts[0] if ha_forecasts else {}
        self.data = {
            "current": current,
            "forecast": ha_forecasts,
        }
        return self.data
