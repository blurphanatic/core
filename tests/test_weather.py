"""Tests for the weather entity."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from homeassistant.components.weather import WeatherEntityFeature

from custom_components.weatherbitch.const import METOFFICE_WEATHER_CODE_MAP
from custom_components.weatherbitch.weather import MetOfficeWeather


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator with sample data."""
    coordinator = MagicMock()
    coordinator.config_entry = MagicMock()
    coordinator.config_entry.entry_id = "test_entry_id"
    coordinator.config_entry.title = "Test Location"
    coordinator.latitude = 51.5074
    coordinator.longitude = -0.1278
    coordinator.data = {
        "forecasts": [
            {
                "time": "2024-01-20T12:00:00Z",
                "screenTemperature": 15.5,
                "feelsLikeTemperature": 13.2,
                "mslp": 1013.25,
                "screenRelativeHumidity": 75,
                "windSpeed10m": 5.5,
                "windGust10m": 8.2,
                "windDirectionFrom10m": 180,
                "visibility": 10000,
                "dewPoint": 10.5,
                "uvIndex": 3,
                "totalCloudAmount": 50,
                "significantWeatherCode": 1,
                "probOfPrecipitation": 20,
                "totalPrecipAmount": 0.5,
            },
            {
                "time": "2024-01-20T15:00:00Z",
                "screenTemperature": 16.0,
                "feelsLikeTemperature": 14.0,
                "mslp": 1012.0,
                "screenRelativeHumidity": 70,
                "windSpeed10m": 6.0,
                "windGust10m": 9.0,
                "windDirectionFrom10m": 190,
                "visibility": 12000,
                "dewPoint": 11.0,
                "uvIndex": 4,
                "totalCloudAmount": 60,
                "significantWeatherCode": 3,
                "probOfPrecipitation": 30,
                "totalPrecipAmount": 1.0,
                "nightMinScreenTemperature": 10.0,
            },
        ]
    }
    return coordinator


@pytest.fixture
def weather_entity(mock_coordinator):
    """Create a weather entity instance."""
    return MetOfficeWeather(mock_coordinator)


class TestWeatherEntityFeatures:
    """Test that WeatherEntityFeature flags are set correctly."""

    def test_supported_features_includes_forecast_daily(self, weather_entity):
        """Test that FORECAST_DAILY feature is enabled."""
        assert (
            weather_entity._attr_supported_features & WeatherEntityFeature.FORECAST_DAILY
        )

    def test_supported_features_includes_forecast_hourly(self, weather_entity):
        """Test that FORECAST_HOURLY feature is enabled."""
        assert (
            weather_entity._attr_supported_features & WeatherEntityFeature.FORECAST_HOURLY
        )

    def test_supported_features_includes_forecast_twice_daily(self, weather_entity):
        """Test that FORECAST_TWICE_DAILY feature is enabled."""
        assert (
            weather_entity._attr_supported_features
            & WeatherEntityFeature.FORECAST_TWICE_DAILY
        )


class TestCurrentConditions:
    """Test current condition properties."""

    def test_native_temperature(self, weather_entity):
        """Test temperature property returns correct value."""
        assert weather_entity.native_temperature == 15.5

    def test_native_apparent_temperature(self, weather_entity):
        """Test feels like temperature property returns correct value."""
        assert weather_entity.native_apparent_temperature == 13.2

    def test_native_pressure(self, weather_entity):
        """Test pressure property returns correct value."""
        assert weather_entity.native_pressure == 1013.25

    def test_humidity(self, weather_entity):
        """Test humidity property returns correct value."""
        assert weather_entity.humidity == 75

    def test_native_wind_speed(self, weather_entity):
        """Test wind speed property returns correct value."""
        assert weather_entity.native_wind_speed == 5.5

    def test_native_wind_gust_speed(self, weather_entity):
        """Test wind gust speed property returns correct value."""
        assert weather_entity.native_wind_gust_speed == 8.2

    def test_wind_bearing(self, weather_entity):
        """Test wind bearing property returns correct value."""
        assert weather_entity.wind_bearing == 180

    def test_native_visibility(self, weather_entity):
        """Test visibility property returns correct value."""
        assert weather_entity.native_visibility == 10000

    def test_native_dew_point(self, weather_entity):
        """Test dew point property returns correct value."""
        assert weather_entity.native_dew_point == 10.5

    def test_uv_index(self, weather_entity):
        """Test UV index property returns correct value."""
        assert weather_entity.uv_index == 3

    def test_cloud_coverage(self, weather_entity):
        """Test cloud coverage property returns correct value."""
        assert weather_entity.cloud_coverage == 50

    def test_condition_mapping(self, weather_entity):
        """Test condition mapping from weather codes."""
        # Weather code 1 = Sunny
        assert weather_entity.condition == METOFFICE_WEATHER_CODE_MAP.get(1)


class TestConditionMapping:
    """Test weather condition mapping from weather codes."""

    def test_clear_night_code(self, mock_coordinator):
        """Test code 0 maps to clear night."""
        mock_coordinator.data["forecasts"][0]["significantWeatherCode"] = 0
        entity = MetOfficeWeather(mock_coordinator)
        assert entity.condition == METOFFICE_WEATHER_CODE_MAP.get(0)

    def test_sunny_code(self, mock_coordinator):
        """Test code 1 maps to sunny."""
        mock_coordinator.data["forecasts"][0]["significantWeatherCode"] = 1
        entity = MetOfficeWeather(mock_coordinator)
        assert entity.condition == METOFFICE_WEATHER_CODE_MAP.get(1)

    def test_rainy_code(self, mock_coordinator):
        """Test code 12 maps to rainy."""
        mock_coordinator.data["forecasts"][0]["significantWeatherCode"] = 12
        entity = MetOfficeWeather(mock_coordinator)
        assert entity.condition == METOFFICE_WEATHER_CODE_MAP.get(12)

    def test_unknown_code_returns_none(self, mock_coordinator):
        """Test unknown code returns None."""
        mock_coordinator.data["forecasts"][0]["significantWeatherCode"] = 999
        entity = MetOfficeWeather(mock_coordinator)
        assert entity.condition is None


class TestForecastMethods:
    """Test async forecast methods."""

    @pytest.mark.asyncio
    async def test_async_forecast_hourly_returns_proper_format(self, weather_entity):
        """Test async_forecast_hourly returns proper Forecast format."""
        forecasts = await weather_entity.async_forecast_hourly()

        assert forecasts is not None
        assert len(forecasts) == 2

        first = forecasts[0]
        assert first["datetime"] == "2024-01-20T12:00:00Z"
        assert first["native_temperature"] == 15.5
        assert first["native_apparent_temperature"] == 13.2
        assert first["humidity"] == 75
        assert first["native_pressure"] == 1013.25
        assert first["native_wind_speed"] == 5.5
        assert first["native_wind_gust_speed"] == 8.2
        assert first["wind_bearing"] == 180
        assert first["precipitation_probability"] == 20
        assert first["native_precipitation"] == 0.5
        assert first["uv_index"] == 3

    @pytest.mark.asyncio
    async def test_async_forecast_daily_includes_native_templow(self, weather_entity):
        """Test async_forecast_daily includes native_templow."""
        forecasts = await weather_entity.async_forecast_daily()

        assert forecasts is not None
        assert len(forecasts) == 2

        # First entry has no tempLow
        assert forecasts[0].get("native_templow") is None

        # Second entry has nightMinScreenTemperature
        assert forecasts[1].get("native_templow") == 10.0

    @pytest.mark.asyncio
    async def test_async_forecast_twice_daily_includes_is_daytime(self, weather_entity):
        """Test async_forecast_twice_daily includes is_daytime."""
        forecasts = await weather_entity.async_forecast_twice_daily()

        assert forecasts is not None
        assert len(forecasts) == 2

        for forecast in forecasts:
            assert "is_daytime" in forecast
            # Default is True when not specified
            assert forecast["is_daytime"] is True


class TestDataStructureFallback:
    """Test fallback to old data structure works."""

    def test_fallback_to_forecasts_key(self, mock_coordinator):
        """Test entity reads from forecasts key when current key is absent."""
        # Data only has forecasts key, no current key
        entity = MetOfficeWeather(mock_coordinator)
        assert entity.native_temperature == 15.5

    def test_current_key_takes_precedence(self, mock_coordinator):
        """Test current key takes precedence over forecasts key."""
        mock_coordinator.data["current"] = {
            "screenTemperature": 20.0,
            "significantWeatherCode": 7,
        }
        entity = MetOfficeWeather(mock_coordinator)
        assert entity.native_temperature == 20.0

    def test_handles_empty_data(self, mock_coordinator):
        """Test entity handles empty data gracefully."""
        mock_coordinator.data = {}
        entity = MetOfficeWeather(mock_coordinator)
        assert entity.native_temperature is None

    def test_handles_none_data(self, mock_coordinator):
        """Test entity handles None data gracefully."""
        mock_coordinator.data = None
        entity = MetOfficeWeather(mock_coordinator)
        assert entity.native_temperature is None


class TestEntityAttributes:
    """Test entity attribute configuration."""

    def test_unique_id_format(self, weather_entity):
        """Test unique ID is properly formatted."""
        assert weather_entity._attr_unique_id == "test_entry_id_weather"

    def test_has_entity_name_is_true(self, weather_entity):
        """Test has_entity_name is enabled."""
        assert weather_entity._attr_has_entity_name is True

    def test_name_is_none(self, weather_entity):
        """Test name is None (uses device name)."""
        assert weather_entity._attr_name is None


class TestUnitConfiguration:
    """Test unit configuration attributes."""

    def test_temperature_unit(self, weather_entity):
        """Test temperature unit is Celsius."""
        from homeassistant.const import UnitOfTemperature

        assert weather_entity._attr_native_temperature_unit == UnitOfTemperature.CELSIUS

    def test_pressure_unit(self, weather_entity):
        """Test pressure unit is hPa."""
        from homeassistant.const import UnitOfPressure

        assert weather_entity._attr_native_pressure_unit == UnitOfPressure.HPA

    def test_wind_speed_unit(self, weather_entity):
        """Test wind speed unit is m/s."""
        from homeassistant.const import UnitOfSpeed

        assert (
            weather_entity._attr_native_wind_speed_unit
            == UnitOfSpeed.METERS_PER_SECOND
        )

    def test_visibility_unit(self, weather_entity):
        """Test visibility unit is meters."""
        from homeassistant.const import UnitOfLength

        assert weather_entity._attr_native_visibility_unit == UnitOfLength.METERS
