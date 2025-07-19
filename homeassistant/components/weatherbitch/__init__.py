"""Met Office DataHub integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ApiError, MetOfficeApiClient
from .const import CONF_API_KEY, DEFAULT_TIMESTEPS, DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.WEATHER]


class MetOfficeDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Met Office data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: MetOfficeApiClient,
        latitude: float,
        longitude: float,
    ) -> None:
        """Initialize the coordinator."""
        self.client = client
        self.latitude = latitude
        self.longitude = longitude
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the API."""
        try:
            data = await self.client.get_point_forecast(
                self.latitude, self.longitude, DEFAULT_TIMESTEPS
            )
        except ApiError as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err

        if not data:
            _LOGGER.warning("No forecast data received")
            raise UpdateFailed("No forecast data received or unexpected format")

        return data


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Met Office from a config entry."""
    api_key = entry.data[CONF_API_KEY]
    latitude = entry.data[CONF_LATITUDE]
    longitude = entry.data[CONF_LONGITUDE]

    client = MetOfficeApiClient(hass, api_key)
    coordinator = MetOfficeDataUpdateCoordinator(hass, client, latitude, longitude)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
