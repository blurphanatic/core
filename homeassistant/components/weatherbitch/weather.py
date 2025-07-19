"""Weather entity for the Met Office integration."""

# pylint: disable=hass-enforce-class-module

from __future__ import annotations

from homeassistant.components.weather import Forecast, WeatherEntity
from homeassistant.util import dt as dt_util
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
        current = self.coordinator.data.get("forecasts", [{}])[0]
        code = current.get("significantWeatherCode")
        return METOFFICE_WEATHER_CODE_MAP.get(code, "unknown")

    @property
    def temperature(self) -> float | None:
        """Return temperature."""
        current = self.coordinator.data.get("forecasts", [{}])[0]
        return current.get("screenTemperature")

    @property
    def pressure(self) -> float | None:
        """Return pressure."""
        current = self.coordinator.data.get("forecasts", [{}])[0]
        return current.get("mslp")

    @property
    def humidity(self) -> int | None:
        """Return humidity."""
        current = self.coordinator.data.get("forecasts", [{}])[0]
        return current.get("screenRelativeHumidity")

    @property
    def wind_speed(self) -> float | None:
        """Return wind speed."""
        current = self.coordinator.data.get("forecasts", [{}])[0]
        return current.get("windSpeed10m")

    @property
    def wind_bearing(self) -> float | None:
        """Return wind bearing."""
        current = self.coordinator.data.get("forecasts", [{}])[0]
        return current.get("windDirectionFrom10m")

    @property
    def forecast(self) -> list[Forecast]:
        """Return the forecast in Home Assistant format."""
        forecasts = self.coordinator.data.get("forecasts", [])
        return [
            {
                "datetime": dt_util.parse_datetime(item.get("time")),
                "condition": METOFFICE_WEATHER_CODE_MAP.get(
                    item.get("significantWeatherCode"), "unknown"
                ),
                "temperature": item.get("screenTemperature"),
                "humidity": item.get("screenRelativeHumidity"),
                "pressure": item.get("mslp"),
                "wind_speed": item.get("windSpeed10m"),
                "wind_bearing": item.get("windDirectionFrom10m"),
            }
            for item in forecasts
        ]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Met Office weather entity."""
    coordinator: MetOfficeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MetOfficeWeather(coordinator)])
