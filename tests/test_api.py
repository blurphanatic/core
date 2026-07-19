"""Tests for the Met Office API client."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed

from custom_components.weatherbitch.api import ApiError, MetOfficeApiClient
from custom_components.weatherbitch.const import (
    BASE_URL,
    DATA_SOURCE,
    FORECAST_TYPE_DAILY,
    FORECAST_TYPE_HOURLY,
)


@pytest.fixture
def mock_hass() -> MagicMock:
    """Create a mock Home Assistant instance."""
    return MagicMock(spec=HomeAssistant)


@pytest.fixture
def api_client(mock_hass: MagicMock) -> MetOfficeApiClient:
    """Create an API client with mocked dependencies."""
    with patch(
        "custom_components.weatherbitch.api.get_async_client"
    ) as mock_get_client:
        mock_http_client = AsyncMock()
        mock_get_client.return_value = mock_http_client
        client = MetOfficeApiClient(mock_hass, "test_api_key")
        client.client = mock_http_client
        return client


class TestMetOfficeApiClientHeaders:
    """Tests for API header construction."""

    def test_get_headers_includes_apikey(self, api_client: MetOfficeApiClient) -> None:
        """Test that headers include the apikey in lowercase."""
        headers = api_client._get_headers()
        assert "apikey" in headers
        assert headers["apikey"] == "test_api_key"

    def test_get_headers_includes_accept(self, api_client: MetOfficeApiClient) -> None:
        """Test that headers include application/json accept type."""
        headers = api_client._get_headers()
        assert "accept" in headers
        assert headers["accept"] == "application/json"

    def test_get_headers_no_ibm_headers(self, api_client: MetOfficeApiClient) -> None:
        """Test that headers do not include any IBM-specific headers."""
        headers = api_client._get_headers()
        # Ensure no IBM or OAuth headers are present
        for key in headers:
            assert "ibm" not in key.lower()
            assert "oauth" not in key.lower()


class TestGetPointForecast:
    """Tests for the get_point_forecast method."""

    @pytest.mark.asyncio
    async def test_get_point_forecast_constructs_correct_url(
        self, api_client: MetOfficeApiClient
    ) -> None:
        """Test that the forecast URL is constructed correctly."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"features": []}
        mock_response.raise_for_status = MagicMock()
        mock_response.text = "{}"
        api_client.client.get = AsyncMock(return_value=mock_response)

        await api_client.get_point_forecast(51.5074, -0.1278, "hourly")

        call_args = api_client.client.get.call_args
        called_url = call_args[1]["url"] if "url" in call_args[1] else call_args[0][0]
        assert f"{BASE_URL}/point/hourly" == called_url

    @pytest.mark.asyncio
    async def test_get_point_forecast_includes_data_source(
        self, api_client: MetOfficeApiClient
    ) -> None:
        """Test that dataSource parameter is included in requests."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"features": []}
        mock_response.raise_for_status = MagicMock()
        mock_response.text = "{}"
        api_client.client.get = AsyncMock(return_value=mock_response)

        await api_client.get_point_forecast(51.5074, -0.1278, "hourly")

        call_args = api_client.client.get.call_args
        params = call_args[1]["params"]
        assert params["dataSource"] == DATA_SOURCE

    @pytest.mark.asyncio
    async def test_get_point_forecast_includes_coordinates(
        self, api_client: MetOfficeApiClient
    ) -> None:
        """Test that latitude and longitude are included in requests."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"features": []}
        mock_response.raise_for_status = MagicMock()
        mock_response.text = "{}"
        api_client.client.get = AsyncMock(return_value=mock_response)

        await api_client.get_point_forecast(51.5074, -0.1278, "hourly")

        call_args = api_client.client.get.call_args
        params = call_args[1]["params"]
        assert params["latitude"] == "51.5074"
        assert params["longitude"] == "-0.1278"


class TestGetAllForecasts:
    """Tests for the get_all_forecasts method."""

    @pytest.mark.asyncio
    async def test_get_all_forecasts_calls_both_endpoints(
        self, api_client: MetOfficeApiClient
    ) -> None:
        """Test that get_all_forecasts calls both hourly and daily endpoints."""
        hourly_response = {
            "features": [{"properties": {"timeSeries": [{"time": "2025-01-20T12:00:00Z"}]}}]
        }
        daily_response = {
            "features": [{"properties": {"timeSeries": [{"time": "2025-01-20T00:00:00Z"}]}}]
        }

        call_count = 0

        async def mock_get_forecast(lat, lon, timesteps):
            nonlocal call_count
            call_count += 1
            if timesteps == FORECAST_TYPE_HOURLY:
                return hourly_response
            return daily_response

        api_client.get_point_forecast = AsyncMock(side_effect=mock_get_forecast)

        result = await api_client.get_all_forecasts(51.5074, -0.1278)

        assert call_count == 2
        assert FORECAST_TYPE_HOURLY in result
        assert FORECAST_TYPE_DAILY in result

    @pytest.mark.asyncio
    async def test_get_all_forecasts_returns_both_responses(
        self, api_client: MetOfficeApiClient
    ) -> None:
        """Test that get_all_forecasts returns both hourly and daily data."""
        hourly_data = {"features": [{"properties": {"timeSeries": [{"id": "hourly"}]}}]}
        daily_data = {"features": [{"properties": {"timeSeries": [{"id": "daily"}]}}]}

        async def mock_get_forecast(lat, lon, timesteps):
            if timesteps == FORECAST_TYPE_HOURLY:
                return hourly_data
            return daily_data

        api_client.get_point_forecast = AsyncMock(side_effect=mock_get_forecast)

        result = await api_client.get_all_forecasts(51.5074, -0.1278)

        assert result[FORECAST_TYPE_HOURLY] == hourly_data
        assert result[FORECAST_TYPE_DAILY] == daily_data

    @pytest.mark.asyncio
    async def test_get_all_forecasts_propagates_api_error(
        self, api_client: MetOfficeApiClient
    ) -> None:
        """Test that API errors are properly propagated."""
        api_client.get_point_forecast = AsyncMock(
            side_effect=ApiError("Test API error")
        )

        with pytest.raises(ApiError, match="Test API error"):
            await api_client.get_all_forecasts(51.5074, -0.1278)


class TestApiErrorHandling:
    """Tests for API error handling."""

    @pytest.mark.asyncio
    async def test_401_raises_config_entry_auth_failed(
        self, api_client: MetOfficeApiClient
    ) -> None:
        """Test that 401 status raises ConfigEntryAuthFailed."""
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        error = httpx.HTTPStatusError(
            "401", request=MagicMock(), response=mock_response
        )
        api_client.client.get = AsyncMock(side_effect=error)

        with pytest.raises(ConfigEntryAuthFailed):
            await api_client.get_point_forecast(51.5074, -0.1278, "hourly")

    @pytest.mark.asyncio
    async def test_500_raises_api_error(
        self, api_client: MetOfficeApiClient
    ) -> None:
        """Test that 500 status raises ApiError."""
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        error = httpx.HTTPStatusError(
            "500", request=MagicMock(), response=mock_response
        )
        api_client.client.get = AsyncMock(side_effect=error)

        with pytest.raises(ApiError, match="HTTP Error 500"):
            await api_client.get_point_forecast(51.5074, -0.1278, "hourly")

    @pytest.mark.asyncio
    async def test_network_error_raises_api_error(
        self, api_client: MetOfficeApiClient
    ) -> None:
        """Test that network errors raise ApiError."""
        import httpx

        api_client.client.get = AsyncMock(
            side_effect=httpx.RequestError("Connection failed")
        )

        with pytest.raises(ApiError, match="Network connection failed"):
            await api_client.get_point_forecast(51.5074, -0.1278, "hourly")

    @pytest.mark.asyncio
    async def test_invalid_json_raises_api_error(
        self, api_client: MetOfficeApiClient
    ) -> None:
        """Test that invalid JSON responses raise ApiError."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.text = "not valid json"
        mock_response.json.side_effect = ValueError("Invalid JSON")
        api_client.client.get = AsyncMock(return_value=mock_response)

        with pytest.raises(ApiError, match="Invalid API response format"):
            await api_client.get_point_forecast(51.5074, -0.1278, "hourly")
