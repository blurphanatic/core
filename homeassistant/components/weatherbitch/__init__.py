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

from .api import ApiError, MetOfficeApiClient
from .const import (
    API_CALL_COUNTER_KEY,
    CONF_API_KEY,
    CONF_TIMESTEPS,
    CONF_UPDATE_INTERVAL,
    DOMAIN,
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
            data = await self.client.get_point_forecast(
                self.latitude, self.longitude, self.timesteps
            )
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
        except ApiError as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err

        if not data or "forecasts" not in data:
            _LOGGER.warning("No forecast data received or unexpected format: %s", data)
            raise UpdateFailed("No forecast data received or unexpected format")

        forecasts = data.get("forecasts")
        if not isinstance(forecasts, list) or not forecasts:
            _LOGGER.warning("Forecast list missing or empty: %s", forecasts)
            raise UpdateFailed("Missing forecast entries")

        expected_keys = {
            "time",
            "screenTemperature",
            "feelsLikeTemperature",
            "probOfPrecipitation",
            "windDirectionFrom10m",
            "windSpeed10m",
            "windGust10m",
            "screenRelativeHumidity",
            "mslp",
            "uvIndex",
            "visibility",
            "significantWeatherCode",
        }
        missing = [key for key in expected_keys if key not in forecasts[0]]
        if missing:
            _LOGGER.warning("Missing expected forecast keys: %s", missing)

        return data
