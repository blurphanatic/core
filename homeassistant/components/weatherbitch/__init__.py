"""The Met Office integration."""

# pylint: disable=hass-enforce-class-module

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ApiError, MetOfficeApiClient
from .const import CONF_API_KEY, DEFAULT_TIMESTEPS, DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.WEATHER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Met Office entry."""
    api_key = entry.data[CONF_API_KEY]
    latitude = entry.data[CONF_LATITUDE]
    longitude = entry.data[CONF_LONGITUDE]

    client = MetOfficeApiClient(hass, api_key)
    coordinator = MetOfficeDataUpdateCoordinator(
        hass, client, latitude, longitude, entry
    )
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
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
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        self.client = client
        self.latitude = latitude
        self.longitude = longitude
        self.config_entry: ConfigEntry = config_entry
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=UPDATE_INTERVAL)
        self.data: dict[str, Any] = {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch latest data from Met Office."""
        try:
            data = await self.client.get_point_forecast(
                self.latitude, self.longitude, DEFAULT_TIMESTEPS
            )
        except ApiError as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err

        if not data or "forecasts" not in data:
            _LOGGER.warning("No forecast data received or unexpected format: %s", data)
            raise UpdateFailed("No forecast data received or unexpected format")

        return data
