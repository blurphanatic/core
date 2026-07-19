"""Tests for the data coordinator."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.weatherbitch import MetOfficeDataUpdateCoordinator
from custom_components.weatherbitch.api import ApiError, MetOfficeApiClient
from custom_components.weatherbitch.const import (
    API_CALL_COUNTER_KEY,
    DOMAIN,
    FIELD_DAY_MAX_TEMP,
    FIELD_DAY_PRECIP_PROB,
    FIELD_DAY_WEATHER_CODE,
    FIELD_NIGHT_MIN_TEMP,
    FIELD_NIGHT_PRECIP_PROB,
    FIELD_NIGHT_WEATHER_CODE,
    FORECAST_TYPE_DAILY,
    FORECAST_TYPE_HOURLY,
    FORECAST_TYPE_TWICE_DAILY,
)


@pytest.fixture
def mock_hass() -> MagicMock:
    """Create a mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {
        DOMAIN: {
            API_CALL_COUNTER_KEY: {
                "count": 0,
                "last_reset_date": datetime.now(UTC).date(),
            }
        }
    }
    return hass


@pytest.fixture
def mock_config_entry() -> MagicMock:
    """Create a mock config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.title = "Test Location"
    entry.entry_id = "test_entry_id"
    return entry


@pytest.fixture
def mock_api_client() -> MagicMock:
    """Create a mock API client."""
    return MagicMock(spec=MetOfficeApiClient)


@pytest.fixture
def coordinator(
    mock_hass: MagicMock,
    mock_api_client: MagicMock,
    mock_config_entry: MagicMock,
) -> MetOfficeDataUpdateCoordinator:
    """Create a coordinator for testing."""
    return MetOfficeDataUpdateCoordinator(
        hass=mock_hass,
        client=mock_api_client,
        latitude=51.5074,
        longitude=-0.1278,
        timesteps="hourly",
        update_interval_td=timedelta(minutes=15),
        config_entry=mock_config_entry,
    )


def create_hourly_response(entries: list[dict] | None = None) -> dict:
    """Create a mock hourly API response."""
    if entries is None:
        entries = [
            {
                "time": "2025-01-20T12:00:00Z",
                "screenTemperature": 10.5,
                "feelsLikeTemperature": 8.2,
                "probOfPrecipitation": 20,
                "windDirectionFrom10m": 180,
                "windSpeed10m": 5.5,
                "windGust10m": 8.0,
                "screenRelativeHumidity": 75,
                "mslp": 101325,  # Pascals
                "uvIndex": 2,
                "visibility": 10000,
                "significantWeatherCode": 1,
            }
        ]
    return {"features": [{"properties": {"timeSeries": entries}}]}


def create_daily_response(entries: list[dict] | None = None) -> dict:
    """Create a mock daily API response."""
    if entries is None:
        entries = [
            {
                "time": "2025-01-20T00:00:00Z",
                FIELD_DAY_MAX_TEMP: 12.0,
                FIELD_NIGHT_MIN_TEMP: 5.0,
                "dayMaxFeelsLikeTemp": 10.0,
                "nightMinFeelsLikeTemp": 3.0,
                FIELD_DAY_WEATHER_CODE: 3,
                FIELD_NIGHT_WEATHER_CODE: 0,
                FIELD_DAY_PRECIP_PROB: 30,
                FIELD_NIGHT_PRECIP_PROB: 10,
                "middayMslp": 101500,  # Pascals
                "midnightMslp": 101600,
                "midday10MWindSpeed": 6.0,
                "midday10MWindDirection": 270,
                "midday10MWindGust": 10.0,
                "midnight10MWindSpeed": 3.0,
                "midnight10MWindDirection": 260,
                "midnight10MWindGust": 5.0,
                "middayVisibility": 15000,
                "midnightVisibility": 8000,
                "middayRelativeHumidity": 65,
                "midnightRelativeHumidity": 85,
                "maxUvIndex": 3,
            }
        ]
    return {"features": [{"properties": {"timeSeries": entries}}]}


class TestCoordinatorHourlyProcessing:
    """Tests for hourly forecast processing."""

    @pytest.mark.asyncio
    async def test_processes_hourly_data_correctly(
        self, coordinator: MetOfficeDataUpdateCoordinator
    ) -> None:
        """Test that hourly data is processed and returned correctly."""
        coordinator.client.get_all_forecasts = AsyncMock(
            return_value={
                FORECAST_TYPE_HOURLY: create_hourly_response(),
                FORECAST_TYPE_DAILY: create_daily_response(),
            }
        )

        result = await coordinator._async_update_data()

        assert FORECAST_TYPE_HOURLY in result
        assert len(result[FORECAST_TYPE_HOURLY]) == 1
        hourly_entry = result[FORECAST_TYPE_HOURLY][0]
        assert hourly_entry["screenTemperature"] == 10.5
        assert hourly_entry["feelsLikeTemperature"] == 8.2

    @pytest.mark.asyncio
    async def test_pressure_conversion_pa_to_hpa(
        self, coordinator: MetOfficeDataUpdateCoordinator
    ) -> None:
        """Test that pressure is converted from Pa to hPa."""
        coordinator.client.get_all_forecasts = AsyncMock(
            return_value={
                FORECAST_TYPE_HOURLY: create_hourly_response(),
                FORECAST_TYPE_DAILY: create_daily_response(),
            }
        )

        result = await coordinator._async_update_data()

        hourly_entry = result[FORECAST_TYPE_HOURLY][0]
        # 101325 Pa should be 1013.25 hPa
        assert hourly_entry["mslp"] == pytest.approx(1013.25, rel=0.01)

    @pytest.mark.asyncio
    async def test_feels_like_temp_normalization(
        self, coordinator: MetOfficeDataUpdateCoordinator
    ) -> None:
        """Test that feelsLikeTemp is normalized to feelsLikeTemperature."""
        hourly_data = create_hourly_response(
            [
                {
                    "time": "2025-01-20T12:00:00Z",
                    "screenTemperature": 10.0,
                    "feelsLikeTemp": 7.5,  # Three-hourly format
                    "probOfPrecipitation": 20,
                    "windDirectionFrom10m": 180,
                    "windSpeed10m": 5.5,
                    "windGust10m": 8.0,
                    "screenRelativeHumidity": 75,
                    "mslp": 101325,
                    "uvIndex": 2,
                    "visibility": 10000,
                    "significantWeatherCode": 1,
                }
            ]
        )

        coordinator.client.get_all_forecasts = AsyncMock(
            return_value={
                FORECAST_TYPE_HOURLY: hourly_data,
                FORECAST_TYPE_DAILY: create_daily_response(),
            }
        )

        result = await coordinator._async_update_data()

        hourly_entry = result[FORECAST_TYPE_HOURLY][0]
        assert hourly_entry["feelsLikeTemperature"] == 7.5


class TestCoordinatorDailyProcessing:
    """Tests for daily forecast processing."""

    @pytest.mark.asyncio
    async def test_daily_temp_high_and_low_extracted(
        self, coordinator: MetOfficeDataUpdateCoordinator
    ) -> None:
        """Test that temp_high and temp_low are properly extracted for daily."""
        coordinator.client.get_all_forecasts = AsyncMock(
            return_value={
                FORECAST_TYPE_HOURLY: create_hourly_response(),
                FORECAST_TYPE_DAILY: create_daily_response(),
            }
        )

        result = await coordinator._async_update_data()

        assert FORECAST_TYPE_DAILY in result
        daily_entry = result[FORECAST_TYPE_DAILY][0]
        assert daily_entry["temp_high"] == 12.0
        assert daily_entry["temp_low"] == 5.0

    @pytest.mark.asyncio
    async def test_daily_screen_temperature_is_average(
        self, coordinator: MetOfficeDataUpdateCoordinator
    ) -> None:
        """Test that daily screenTemperature is average of max and min."""
        coordinator.client.get_all_forecasts = AsyncMock(
            return_value={
                FORECAST_TYPE_HOURLY: create_hourly_response(),
                FORECAST_TYPE_DAILY: create_daily_response(),
            }
        )

        result = await coordinator._async_update_data()

        daily_entry = result[FORECAST_TYPE_DAILY][0]
        # (12.0 + 5.0) / 2 = 8.5
        assert daily_entry["screenTemperature"] == pytest.approx(8.5, rel=0.01)

    @pytest.mark.asyncio
    async def test_daily_pressure_conversion(
        self, coordinator: MetOfficeDataUpdateCoordinator
    ) -> None:
        """Test that daily pressure is converted from Pa to hPa."""
        coordinator.client.get_all_forecasts = AsyncMock(
            return_value={
                FORECAST_TYPE_HOURLY: create_hourly_response(),
                FORECAST_TYPE_DAILY: create_daily_response(),
            }
        )

        result = await coordinator._async_update_data()

        daily_entry = result[FORECAST_TYPE_DAILY][0]
        # 101500 Pa should be 1015.0 hPa
        assert daily_entry["mslp"] == pytest.approx(1015.0, rel=0.01)


class TestCoordinatorTwiceDailyProcessing:
    """Tests for twice-daily forecast processing."""

    @pytest.mark.asyncio
    async def test_builds_twice_daily_from_daily(
        self, coordinator: MetOfficeDataUpdateCoordinator
    ) -> None:
        """Test that twice-daily forecasts are built from daily data."""
        coordinator.client.get_all_forecasts = AsyncMock(
            return_value={
                FORECAST_TYPE_HOURLY: create_hourly_response(),
                FORECAST_TYPE_DAILY: create_daily_response(),
            }
        )

        result = await coordinator._async_update_data()

        assert FORECAST_TYPE_TWICE_DAILY in result
        # 1 daily entry should produce 2 twice-daily entries
        assert len(result[FORECAST_TYPE_TWICE_DAILY]) == 2

    @pytest.mark.asyncio
    async def test_twice_daily_day_entry(
        self, coordinator: MetOfficeDataUpdateCoordinator
    ) -> None:
        """Test that day entry has correct values and is_daytime=True."""
        coordinator.client.get_all_forecasts = AsyncMock(
            return_value={
                FORECAST_TYPE_HOURLY: create_hourly_response(),
                FORECAST_TYPE_DAILY: create_daily_response(),
            }
        )

        result = await coordinator._async_update_data()

        day_entry = result[FORECAST_TYPE_TWICE_DAILY][0]
        assert day_entry["is_daytime"] is True
        assert day_entry["temperature"] == 12.0
        assert day_entry["precipitation_probability"] == 30
        assert day_entry["weather_code"] == 3

    @pytest.mark.asyncio
    async def test_twice_daily_night_entry(
        self, coordinator: MetOfficeDataUpdateCoordinator
    ) -> None:
        """Test that night entry has correct values and is_daytime=False."""
        coordinator.client.get_all_forecasts = AsyncMock(
            return_value={
                FORECAST_TYPE_HOURLY: create_hourly_response(),
                FORECAST_TYPE_DAILY: create_daily_response(),
            }
        )

        result = await coordinator._async_update_data()

        night_entry = result[FORECAST_TYPE_TWICE_DAILY][1]
        assert night_entry["is_daytime"] is False
        assert night_entry["temperature"] == 5.0
        assert night_entry["precipitation_probability"] == 10
        assert night_entry["weather_code"] == 0

    @pytest.mark.asyncio
    async def test_twice_daily_uses_correct_wind_data(
        self, coordinator: MetOfficeDataUpdateCoordinator
    ) -> None:
        """Test that twice-daily uses midday wind for day and midnight for night."""
        coordinator.client.get_all_forecasts = AsyncMock(
            return_value={
                FORECAST_TYPE_HOURLY: create_hourly_response(),
                FORECAST_TYPE_DAILY: create_daily_response(),
            }
        )

        result = await coordinator._async_update_data()

        day_entry = result[FORECAST_TYPE_TWICE_DAILY][0]
        night_entry = result[FORECAST_TYPE_TWICE_DAILY][1]

        # Day uses midday wind values
        assert day_entry["windSpeed10m"] == 6.0
        assert day_entry["windDirectionFrom10m"] == 270

        # Night uses midnight wind values
        assert night_entry["windSpeed10m"] == 3.0
        assert night_entry["windDirectionFrom10m"] == 260


class TestCoordinatorBackwardCompatibility:
    """Tests for backward compatibility."""

    @pytest.mark.asyncio
    async def test_forecasts_key_present(
        self, coordinator: MetOfficeDataUpdateCoordinator
    ) -> None:
        """Test that 'forecasts' key is present for backward compatibility."""
        coordinator.client.get_all_forecasts = AsyncMock(
            return_value={
                FORECAST_TYPE_HOURLY: create_hourly_response(),
                FORECAST_TYPE_DAILY: create_daily_response(),
            }
        )

        result = await coordinator._async_update_data()

        assert "forecasts" in result

    @pytest.mark.asyncio
    async def test_forecasts_equals_hourly(
        self, coordinator: MetOfficeDataUpdateCoordinator
    ) -> None:
        """Test that 'forecasts' is the same as hourly data."""
        coordinator.client.get_all_forecasts = AsyncMock(
            return_value={
                FORECAST_TYPE_HOURLY: create_hourly_response(),
                FORECAST_TYPE_DAILY: create_daily_response(),
            }
        )

        result = await coordinator._async_update_data()

        assert result["forecasts"] == result[FORECAST_TYPE_HOURLY]

    @pytest.mark.asyncio
    async def test_current_is_first_hourly_entry(
        self, coordinator: MetOfficeDataUpdateCoordinator
    ) -> None:
        """Test that 'current' contains the first hourly entry."""
        coordinator.client.get_all_forecasts = AsyncMock(
            return_value={
                FORECAST_TYPE_HOURLY: create_hourly_response(),
                FORECAST_TYPE_DAILY: create_daily_response(),
            }
        )

        result = await coordinator._async_update_data()

        assert "current" in result
        assert result["current"]["screenTemperature"] == 10.5


class TestCoordinatorErrorHandling:
    """Tests for error handling in the coordinator."""

    @pytest.mark.asyncio
    async def test_api_error_raises_update_failed(
        self, coordinator: MetOfficeDataUpdateCoordinator
    ) -> None:
        """Test that ApiError is wrapped in UpdateFailed."""
        coordinator.client.get_all_forecasts = AsyncMock(
            side_effect=ApiError("Test error")
        )

        with pytest.raises(UpdateFailed, match="Error fetching data"):
            await coordinator._async_update_data()

    @pytest.mark.asyncio
    async def test_missing_features_raises_update_failed(
        self, coordinator: MetOfficeDataUpdateCoordinator
    ) -> None:
        """Test that missing features raises UpdateFailed."""
        coordinator.client.get_all_forecasts = AsyncMock(
            return_value={
                FORECAST_TYPE_HOURLY: {"features": []},
                FORECAST_TYPE_DAILY: create_daily_response(),
            }
        )

        with pytest.raises(UpdateFailed, match="Missing features"):
            await coordinator._async_update_data()

    @pytest.mark.asyncio
    async def test_missing_time_series_raises_update_failed(
        self, coordinator: MetOfficeDataUpdateCoordinator
    ) -> None:
        """Test that missing timeSeries raises UpdateFailed."""
        coordinator.client.get_all_forecasts = AsyncMock(
            return_value={
                FORECAST_TYPE_HOURLY: {"features": [{"properties": {"timeSeries": []}}]},
                FORECAST_TYPE_DAILY: create_daily_response(),
            }
        )

        with pytest.raises(UpdateFailed, match="Missing timeSeries"):
            await coordinator._async_update_data()


class TestApiCallCounter:
    """Tests for API call counting."""

    @pytest.mark.asyncio
    async def test_increments_call_counter_by_two(
        self, coordinator: MetOfficeDataUpdateCoordinator
    ) -> None:
        """Test that call counter increments by 2 (hourly + daily)."""
        coordinator.client.get_all_forecasts = AsyncMock(
            return_value={
                FORECAST_TYPE_HOURLY: create_hourly_response(),
                FORECAST_TYPE_DAILY: create_daily_response(),
            }
        )

        initial_count = coordinator.hass.data[DOMAIN][API_CALL_COUNTER_KEY]["count"]
        await coordinator._async_update_data()
        final_count = coordinator.hass.data[DOMAIN][API_CALL_COUNTER_KEY]["count"]

        assert final_count == initial_count + 2

    @pytest.mark.asyncio
    async def test_resets_counter_on_new_day(
        self,
        mock_hass: MagicMock,
        mock_api_client: MagicMock,
        mock_config_entry: MagicMock,
    ) -> None:
        """Test that counter resets when date changes."""
        # Set counter to yesterday with some calls
        yesterday = datetime.now(UTC).date() - timedelta(days=1)
        mock_hass.data[DOMAIN][API_CALL_COUNTER_KEY] = {
            "count": 50,
            "last_reset_date": yesterday,
        }

        coordinator = MetOfficeDataUpdateCoordinator(
            hass=mock_hass,
            client=mock_api_client,
            latitude=51.5074,
            longitude=-0.1278,
            timesteps="hourly",
            update_interval_td=timedelta(minutes=15),
            config_entry=mock_config_entry,
        )

        coordinator.client.get_all_forecasts = AsyncMock(
            return_value={
                FORECAST_TYPE_HOURLY: create_hourly_response(),
                FORECAST_TYPE_DAILY: create_daily_response(),
            }
        )

        await coordinator._async_update_data()

        # Counter should have been reset to 0 and then incremented by 2
        assert mock_hass.data[DOMAIN][API_CALL_COUNTER_KEY]["count"] == 2
        assert (
            mock_hass.data[DOMAIN][API_CALL_COUNTER_KEY]["last_reset_date"]
            == datetime.now(UTC).date()
        )
