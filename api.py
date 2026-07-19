"""Asynchronous client for the Met Office DataHub API."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

import httpx

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.httpx_client import get_async_client

# Import BASE_URL and DATA_SOURCE from your const.py
from .const import BASE_URL, DATA_SOURCE, FORECAST_TYPE_HOURLY, FORECAST_TYPE_DAILY

_LOGGER = logging.getLogger(__name__)


class ApiError(Exception):
    """MIKEY WUZ HERE CONFIRMED Raised when the API request fails."""


class MetOfficeApiClient:
    """Client for interacting with the Met Office point forecast API."""

    def __init__(self, hass: HomeAssistant, api_key: str) -> None:
        """Initialize the API client.

        Args:
            hass: The Home Assistant instance.
            api_key: The Met Office DataHub API key.
        """
        self.api_key = api_key
        # BASE_URL is imported from const.py for consistency
        self.base_url = BASE_URL
        self.client = get_async_client(hass)

    def _get_headers(self) -> dict[str, str]:
        """Return headers required for the API request."""
        return {"apikey": self.api_key, "accept": "application/json"}

    async def _make_request(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        """Perform a GET request to the API with given parameters.

        Args:
            url: The full URL for the API request.
            params: Dictionary of query parameters for the request.

        Returns:
            A dictionary containing the JSON response from the API.

        Raises:
            ConfigEntryAuthFailed: If authentication fails (401 status code).
            ApiError: For other HTTP errors or network connection issues.
            json.JSONDecodeError: If the API response is not valid JSON.
        """
        _LOGGER.debug(
            "Met Office API Request: URL=%s, Headers=%s, Params=%s",
            url,
            self._get_headers(),
            params,
        )
        start_time = time.monotonic()
        try:
            response = await self.client.get(
                url, headers=self._get_headers(), params=params
            )
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            end_time = time.monotonic()
            duration_ms = round((end_time - start_time) * 1000)
            _LOGGER.info(
                "Met Office API call to %s successful in %d ms",
                url.split("?")[0],  # Log base URL without query params for clarity
                duration_ms,
            )
            _LOGGER.debug("Met Office API Response Body: %s", response.text)  # Log raw response body
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            text = exc.response.text
            _LOGGER.error("API request failed: %s - %s", status, text)
            if status == 401:
                raise ConfigEntryAuthFailed("Invalid API Key") from exc
            raise ApiError(f"HTTP Error {status}: {text}") from exc
        except httpx.RequestError as exc:
            _LOGGER.error("Network error during API request: %s", exc)
            raise ApiError("Network connection failed") from exc

        try:
            return response.json()
        except json.JSONDecodeError as exc:
            _LOGGER.error("Invalid JSON response from API: %s", exc)
            raise ApiError("Invalid API response format") from exc

    async def get_point_forecast(
        self, latitude: float, longitude: float, timesteps: str = "hourly"
    ) -> dict[str, Any]:
        """Retrieve probabilistic forecast for a latitude/longitude.

        Args:
            latitude: The latitude of the forecast location.
            longitude: The longitude of the forecast location.
            timesteps: The forecast frequency (e.g., "hourly", "three-hourly", "daily").

        Returns:
            A dictionary containing the raw JSON forecast data.

        Raises:
            ApiError: If the API request fails.
        """
        # Construct the full URL with timesteps as a path segment (e.g., /point/hourly)
        full_url = f"{self.base_url}/point/{timesteps}"

        params = {
            "latitude": str(latitude),
            "longitude": str(longitude),
            "dataSource": DATA_SOURCE,  # Mandatory parameter for this API
            "excludeParameterMetadata": "FALSE",
            "includeLocationName": "TRUE",
            # "timesteps" is NOT included here as it's part of the URL path
        }
        try:
            # Pass the constructed full_url to _make_request
            return await self._make_request(url=full_url, params=params)
        except ApiError as err:
            _LOGGER.error("Point forecast request failed: %s", err)
            raise

    async def get_all_forecasts(
        self, latitude: float, longitude: float
    ) -> dict[str, Any]:
        """Fetch hourly and daily forecasts in parallel.

        This method fetches both hourly and daily forecast data simultaneously
        using asyncio.gather for optimal performance. The results are returned
        as a dictionary with 'hourly' and 'daily' keys containing raw API responses.

        Args:
            latitude: The latitude of the forecast location.
            longitude: The longitude of the forecast location.

        Returns:
            A dictionary with keys 'hourly' and 'daily' containing raw API responses.

        Raises:
            ApiError: If any of the API requests fail.
        """
        _LOGGER.debug(
            "Fetching all forecasts (hourly and daily) for lat=%s, lon=%s",
            latitude,
            longitude,
        )

        try:
            # Fetch both forecast types in parallel
            hourly_task = self.get_point_forecast(latitude, longitude, FORECAST_TYPE_HOURLY)
            daily_task = self.get_point_forecast(latitude, longitude, FORECAST_TYPE_DAILY)

            hourly_data, daily_data = await asyncio.gather(
                hourly_task, daily_task, return_exceptions=False
            )

            _LOGGER.info(
                "Successfully fetched all forecasts: hourly=%d entries, daily=%d entries",
                len(hourly_data.get("features", [{}])[0].get("properties", {}).get("timeSeries", [])),
                len(daily_data.get("features", [{}])[0].get("properties", {}).get("timeSeries", [])),
            )

            return {
                FORECAST_TYPE_HOURLY: hourly_data,
                FORECAST_TYPE_DAILY: daily_data,
            }
        except ApiError as err:
            _LOGGER.error("Failed to fetch all forecasts: %s", err)
            raise
