"""Weather entity for the Met Office integration."""

# pylint: disable=hass-enforce-class-module

from __future__ import annotations

from homeassistant.components.weather import Forecast, WeatherEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPressure, UnitOfSpeed, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import MetOfficeDataUpdateCoordinator, get_device_info
from .const import DOMAIN, METOFFICE_WEATHER_CODE_MAP


class MetOfficeEntity(CoordinatorEntity[MetOfficeDataUpdateCoordinator]):
    """Base class for Met Office entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: MetOfficeDataUpdateCoordinator) -> None:
        """Initialize entity."""
        super().__init__(coordinator)
        self._attr_device_info = get_device_info(
            coordinator.latitude, coordinator.longitude, coordinator.config_entry.title
        )


class MetOfficeWeather(MetOfficeEntity, WeatherEntity):
    """Representation of Met Office weather data."""

    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_pressure_unit = UnitOfPressure.HPA
    _attr_wind_speed_unit = UnitOfSpeed.METERS_PER_SECOND

    def __init__(self, coordinator: MetOfficeDataUpdateCoordinator) -> None:
        """Initialize weather entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_weather"

    @property
    def condition(self) -> str | None:
        """Return current weather condition."""
        code = self.coordinator.data.get("current", {}).get("weather_code")
        return METOFFICE_WEATHER_CODE_MAP.get(code, "unknown")

    @property
    def temperature(self) -> float | None:
        """Return temperature."""
        return self.coordinator.data.get("current", {}).get("temperature")

    @property
    def pressure(self) -> float | None:
        """Return pressure."""
        return self.coordinator.data.get("current", {}).get("pressure")

    @property
    def humidity(self) -> int | None:
        """Return humidity."""
        return self.coordinator.data.get("current", {}).get("humidity")

    @property
    def wind_speed(self) -> float | None:
        """Return wind speed."""
        return self.coordinator.data.get("current", {}).get("wind_speed")

    @property
    def wind_bearing(self) -> float | None:
        """Return wind bearing."""
        return self.coordinator.data.get("current", {}).get("wind_bearing")

    @property
    def forecast(self) -> list[Forecast]:
        """Return the forecast in Home Assistant format."""
        return self.coordinator.data.get("forecast", [])


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Met Office weather entity."""
    coordinator: MetOfficeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MetOfficeWeather(coordinator)])
