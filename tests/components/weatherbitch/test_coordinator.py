"""Tests for the Met Office coordinator."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

from homeassistant.components.weatherbitch import MetOfficeDataUpdateCoordinator
from homeassistant.components.weatherbitch.const import API_CALL_COUNTER_KEY, DOMAIN
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry


async def test_update_data_future_filter(hass: HomeAssistant) -> None:
    """Validate future filtering and field mapping."""

    api_response = {
        "features": [
            {
                "properties": {
                    "timeSeries": [
                        {
                            "time": "2024-01-01T09:00Z",
                            "screenTemperature": 5,
                            "feelsLikeTemp": 4,
                            "screenRelativeHumidity": 80,
                            "mslp": 100000,
                            "uvIndex": 1,
                            "visibility": 1000,
                            "significantWeatherCode": 1,
                            "windSpeed10m": 2,
                            "windDirectionFrom10m": 180,
                            "windGustSpeed10m": 3,
                            "precipitationRate": 0,
                            "probOfPrecipitation": 5,
                            "minScreenAirTemp": 4,
                            "maxScreenAirTemp": 6,
                            "totalPrecipAmount": 0.1,
                            "totalSnowAmount": 0,
                            "screenDewPointTemperature": 4,
                        },
                        {
                            "time": "2024-01-01T11:00Z",
                            "screenTemperature": 6,
                            "feelsLikeTemp": 5,
                            "screenRelativeHumidity": 82,
                            "mslp": 100500,
                            "uvIndex": 2,
                            "visibility": 1100,
                            "significantWeatherCode": 2,
                            "windSpeed10m": 3,
                            "windDirectionFrom10m": 190,
                            "windGustSpeed10m": 4,
                            "precipitationRate": 0,
                            "probOfPrecipitation": 10,
                            "minScreenAirTemp": 5,
                            "maxScreenAirTemp": 7,
                            "totalPrecipAmount": 0.0,
                            "totalSnowAmount": 0,
                            "screenDewPointTemperature": 5,
                        },
                        {
                            "time": "2024-01-01T12:00Z",
                            "screenTemperature": 7,
                            "feelsLikeTemp": 6,
                            "screenRelativeHumidity": 83,
                            "mslp": 100800,
                            "uvIndex": 3,
                            "visibility": 1200,
                            "significantWeatherCode": 3,
                            "windSpeed10m": 4,
                            "windDirectionFrom10m": 200,
                            "windGustSpeed10m": 5,
                            "precipitationRate": 0,
                            "probOfPrecipitation": 15,
                            "minScreenAirTemp": 6,
                            "maxScreenAirTemp": 8,
                            "totalPrecipAmount": 0.2,
                            "totalSnowAmount": 0,
                            "screenDewPointTemperature": 6,
                        },
                    ]
                }
            }
        ]
    }

    entry = MockConfigEntry(domain=DOMAIN, title="Test")
    client = Mock()
    client.get_point_forecast = AsyncMock(return_value=api_response)

    coordinator = MetOfficeDataUpdateCoordinator(
        hass, client, 0.0, 0.0, "hourly", timedelta(minutes=15), entry
    )
    hass.data[DOMAIN] = {
        API_CALL_COUNTER_KEY: {
            "count": 0,
            "last_reset_date": datetime(2024, 1, 1, tzinfo=UTC).date(),
        }
    }
    coordinator.config_entry = entry

    with patch(
        "homeassistant.util.dt.utcnow",
        return_value=datetime(2024, 1, 1, 10, tzinfo=UTC),
    ):
        result = await coordinator._async_update_data()

    assert len(result["forecast"]) == 2
    assert result["current"]["temperature"] == 6
    assert result["forecast"][0]["pressure"] == 1005.0
    assert result["current"]["raw"]["mslp"] == 100500
