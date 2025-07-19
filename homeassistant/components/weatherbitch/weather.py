"""Met Office weather entity."""

# pylint: disable=hass-enforce-class-module

from __future__ import annotations

from homeassistant.components.weather import WeatherEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPressure, UnitOfSpeed, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import get_device_info
from .const import DOMAIN, W_CODE_CONDITION_MAP
from .coordinator import MetOfficeDataUpdateCoordinator


class MetOfficeEntity(CoordinatorEntity[MetOfficeDataUpdateCoordinator]):
    """Base class for Met Office entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: MetOfficeDataUpdateCoordinator) -> None:
        """Initialize base entity."""
        super().__init__(coordinator)
        self._attr_device_info = get_device_info(
            coordinator.site_id, coordinator.site_name
        )


class MetOfficeWeather(MetOfficeEntity, WeatherEntity):
    """Representation of Met Office weather data."""

    _attr_name = None
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.METERS_PER_SECOND

    def __init__(self, coordinator: MetOfficeDataUpdateCoordinator) -> None:
        """Initialize the weather entity."""
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.site_id

    @property
    def condition(self) -> str | None:
        """Return current weather condition."""
        code = self.coordinator.data.get("weather")
        return (
            W_CODE_CONDITION_MAP.get(code, "unknown")
            if isinstance(code, int)
            else "unknown"
        )

    @property
    def native_temperature(self) -> float | None:
        """Return current temperature."""
        return self.coordinator.data.get("temperature")

    @property
    def native_pressure(self) -> float | None:
        """Return current pressure."""
        return self.coordinator.data.get("pressure")

    @property
    def humidity(self) -> int | None:
        """Return current humidity."""
        return self.coordinator.data.get("humidity")

    @property
    def uv_index(self) -> int | None:
        """Return current UV index."""
        return self.coordinator.data.get("uv_index")

    @property
    def native_wind_speed(self) -> float | None:
        """Return current wind speed."""
        return self.coordinator.data.get("wind_speed")

    @property
    def wind_bearing(self) -> str | None:
        """Return current wind bearing."""
        return self.coordinator.data.get("wind_direction")

    @property
    def native_wind_gust_speed(self) -> float | None:
        """Return current wind gust speed."""
        return self.coordinator.data.get("wind_gust")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Met Office weather entity."""
    coordinator: MetOfficeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MetOfficeWeather(coordinator)])
