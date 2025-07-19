"""Weather entity for the Met Office integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.weather import WeatherEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPressure, UnitOfSpeed, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from . import MetOfficeDataUpdateCoordinator
from .const import DOMAIN, METOFFICE_WEATHER_CODE_MAP


class MetOfficeWeather(
    CoordinatorEntity[MetOfficeDataUpdateCoordinator], WeatherEntity
):
    """Representation of Met Office weather data."""

    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.METERS_PER_SECOND

    def __init__(
        self, coordinator: MetOfficeDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the weather entity."""
        super().__init__(coordinator)
        self._attr_name = f"{entry.title} Forecast"
        self._attr_unique_id = f"{entry.entry_id}_weather"

    @property
    def condition(self) -> str | None:
        """Return current weather condition."""
        forecast = self.coordinator.data.get("forecasts", [{}])[0]
        code = forecast.get("significantWeatherCode")
        return METOFFICE_WEATHER_CODE_MAP.get(code, "unknown")

    @property
    def temperature(self) -> float | None:
        """Return current temperature."""
        forecast = self.coordinator.data.get("forecasts", [{}])[0]
        return forecast.get("screenTemperature")

    @property
    def humidity(self) -> int | None:
        """Return current humidity."""
        forecast = self.coordinator.data.get("forecasts", [{}])[0]
        return forecast.get("screenRelativeHumidity")

    @property
    def pressure(self) -> float | None:
        """Return current pressure."""
        forecast = self.coordinator.data.get("forecasts", [{}])[0]
        return forecast.get("mslp")

    @property
    def wind_speed(self) -> float | None:
        """Return current wind speed."""
        forecast = self.coordinator.data.get("forecasts", [{}])[0]
        return forecast.get("windSpeed10m")

    @property
    def wind_bearing(self) -> float | None:
        """Return wind bearing."""
        forecast = self.coordinator.data.get("forecasts", [{}])[0]
        return forecast.get("windDirectionFrom10m")

    @property
    def forecast(self) -> list[dict[str, Any]]:
        """Return the forecast data."""
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
    """Set up the Met Office weather entity."""
    coordinator: MetOfficeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MetOfficeWeather(coordinator, entry)])
