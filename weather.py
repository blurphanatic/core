"""Weather entity for the Met Office integration."""

# pylint: disable=hass-enforce-class-module

from __future__ import annotations

from homeassistant.components.weather import (
    Forecast,
    WeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import MetOfficeDataUpdateCoordinator, get_device_info
from .const import (
    DOMAIN,
    FIELD_DAY_MAX_FEELS_LIKE,
    FIELD_DAY_MAX_TEMP,
    FIELD_NIGHT_MIN_TEMP,
    METOFFICE_WEATHER_CODE_MAP,
)


def _first_not_none(*values):
    """Return the first value that is not None.

    Deliberately not `a or b`: a legitimate reading of 0.0 degC is falsy, and
    an `or` chain would silently discard it and fall through to the next source.
    """
    for value in values:
        if value is not None:
            return value
    return None


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
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.METERS_PER_SECOND
    _attr_native_visibility_unit = UnitOfLength.METERS

    # Enable all three forecast types
    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_DAILY
        | WeatherEntityFeature.FORECAST_HOURLY
        | WeatherEntityFeature.FORECAST_TWICE_DAILY
    )

    def __init__(self, coordinator: MetOfficeDataUpdateCoordinator) -> None:
        """Initialize weather entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_weather"

    def _get_current(self) -> dict:
        """Get current conditions from coordinator data.

        Returns the first forecast entry as current conditions.
        Handles both old structure (forecasts key) and potential future
        structure (current key).
        """
        data = self.coordinator.data or {}
        # Try new structure first, fall back to old
        return data.get("current") or data.get("forecasts", [{}])[0]

    @property
    def condition(self) -> str | None:
        """Return current weather condition."""
        current = self._get_current()
        code = current.get("significantWeatherCode")
        return METOFFICE_WEATHER_CODE_MAP.get(code)

    @property
    def native_temperature(self) -> float | None:
        """Return temperature in native units (Celsius)."""
        return self._get_current().get("screenTemperature")

    @property
    def native_apparent_temperature(self) -> float | None:
        """Return feels like temperature in native units (Celsius)."""
        return self._get_current().get("feelsLikeTemperature")

    @property
    def native_pressure(self) -> float | None:
        """Return pressure in native units (hPa)."""
        return self._get_current().get("mslp")

    @property
    def humidity(self) -> int | None:
        """Return humidity percentage."""
        return self._get_current().get("screenRelativeHumidity")

    @property
    def native_wind_speed(self) -> float | None:
        """Return wind speed in native units (m/s)."""
        return self._get_current().get("windSpeed10m")

    @property
    def native_wind_gust_speed(self) -> float | None:
        """Return wind gust speed in native units (m/s)."""
        return self._get_current().get("windGust10m")

    @property
    def wind_bearing(self) -> float | None:
        """Return wind bearing in degrees."""
        return self._get_current().get("windDirectionFrom10m")

    @property
    def native_visibility(self) -> float | None:
        """Return visibility in native units (meters)."""
        return self._get_current().get("visibility")

    @property
    def native_dew_point(self) -> float | None:
        """Return dew point temperature in native units (Celsius)."""
        return self._get_current().get("dewPoint")

    @property
    def uv_index(self) -> float | None:
        """Return UV index."""
        return self._get_current().get("uvIndex")

    @property
    def cloud_coverage(self) -> int | None:
        """Return cloud coverage percentage."""
        return self._get_current().get("totalCloudAmount")

    # Modern forecast service methods

    async def async_forecast_hourly(self) -> list[Forecast] | None:
        """Return hourly forecast.

        Returns the forecast data appropriate for hourly display.
        For hourly timesteps, returns all forecasts.
        For other timesteps, returns available data or empty list.
        """
        data = self.coordinator.data or {}
        # Use hourly key if available, otherwise fall back to forecasts
        hourly = data.get("hourly") or data.get("forecasts", [])
        return self._build_forecast_list(hourly, is_daily=False)

    async def async_forecast_daily(self) -> list[Forecast] | None:
        """Return daily forecast.

        Returns the forecast data appropriate for daily display.
        For daily timesteps, returns all forecasts.
        For other timesteps, returns available data or empty list.
        """
        data = self.coordinator.data or {}
        # Use daily key if available, otherwise fall back to forecasts
        daily = data.get("daily") or data.get("forecasts", [])
        return self._build_forecast_list(daily, is_daily=True)

    async def async_forecast_twice_daily(self) -> list[Forecast] | None:
        """Return twice-daily forecast.

        Returns forecast data with day/night separation.
        """
        data = self.coordinator.data or {}
        # Use twice_daily key if available, otherwise build from forecasts
        twice_daily = data.get("twice_daily") or data.get("forecasts", [])
        return self._build_twice_daily_list(twice_daily)

    def _build_forecast_list(
        self, forecasts: list, is_daily: bool
    ) -> list[Forecast]:
        """Build forecast list for hourly or daily forecasts.

        Args:
            forecasts: List of forecast dictionaries from the API.
            is_daily: Whether this is a daily forecast (includes templow).

        Returns:
            List of Forecast TypedDict entries for Home Assistant.
        """
        result: list[Forecast] = []
        for item in forecasts:
            entry: Forecast = {
                "datetime": item.get("time"),
                "condition": METOFFICE_WEATHER_CODE_MAP.get(
                    item.get("significantWeatherCode")
                ),
                "native_temperature": item.get("screenTemperature"),
                "native_apparent_temperature": item.get("feelsLikeTemperature"),
                "humidity": item.get("screenRelativeHumidity"),
                "native_pressure": item.get("mslp"),
                "native_wind_speed": item.get("windSpeed10m"),
                "native_wind_gust_speed": item.get("windGust10m"),
                "wind_bearing": item.get("windDirectionFrom10m"),
                "precipitation_probability": item.get("probOfPrecipitation"),
                "native_precipitation": item.get("totalPrecipAmount"),
                "uv_index": item.get("uvIndex"),
            }
            if is_daily:
                # A daily forecast's temperature must be the day's MAXIMUM.
                # _process_daily_forecast sets screenTemperature to the mean of
                # dayMax and nightMin "for backward compatibility", so reading it
                # above yields the midpoint: on 19 Jul 2026 that reported 18.0 for
                # a day whose real high was 22.2. Take the explicit day-max and
                # night-min fields instead.
                entry["native_temperature"] = _first_not_none(
                    item.get("temp_high"),
                    item.get(FIELD_DAY_MAX_TEMP),
                    entry.get("native_temperature"),
                )
                entry["native_apparent_temperature"] = _first_not_none(
                    item.get(FIELD_DAY_MAX_FEELS_LIKE),
                    entry.get("native_apparent_temperature"),
                )
                entry["native_templow"] = _first_not_none(
                    item.get("temp_low"),
                    item.get(FIELD_NIGHT_MIN_TEMP),
                    item.get("tempLow"),
                )
            result.append(entry)
        return result

    def _build_twice_daily_list(self, forecasts: list) -> list[Forecast]:
        """Build twice-daily forecast list with day/night separation.

        Args:
            forecasts: List of forecast dictionaries from the API.

        Returns:
            List of Forecast TypedDict entries with is_daytime flag.
        """
        result: list[Forecast] = []
        for item in forecasts:
            entry: Forecast = {
                "datetime": item.get("time"),
                "is_daytime": item.get("is_daytime", True),
                "condition": METOFFICE_WEATHER_CODE_MAP.get(
                    item.get("significantWeatherCode")
                ),
                "native_temperature": item.get("screenTemperature"),
                "precipitation_probability": item.get("probOfPrecipitation"),
            }
            result.append(entry)
        return result


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Met Office weather entity."""
    coordinator: MetOfficeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MetOfficeWeather(coordinator)])
