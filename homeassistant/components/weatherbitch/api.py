"""Asynchronous client for the Met Office DataHub API."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

import httpx

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.httpx_client import get_async_client

from .const import BASE_URL

_LOGGER = logging.getLogger(__name__)


class ApiError(Exception):
    """Raised when the API request fails."""


class MetOfficeApiClient:
    """Client for interacting with the Met Office point forecast API."""

    def __init__(self, hass: HomeAssistant, api_key: str) -> None:
        """Initialize the API client."""
        self.api_key = api_key
        self.base_url = BASE_URL
        self.client = get_async_client(hass)

    def _get_headers(self) -> dict[str, str]:
        """Return headers required for the API request."""
        return {"apikey": self.api_key, "accept": "application/json"}

    async def _make_request(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        """Make a GET request to the API and return the JSON response."""
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
            response.raise_for_status()
            end_time = time.monotonic()
            duration_ms = round((end_time - start_time) * 1000)
            _LOGGER.info(
                "Met Office API call to %s successful in %d ms",
                url.split("?")[0],
                duration_ms,
            )
            _LOGGER.debug("Met Office API Response Body: %s", response.text)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                _LOGGER.error("Authentication failed: %s", exc.response.text)
                raise ConfigEntryAuthFailed("Invalid API Key") from exc
            _LOGGER.error(
                "API request failed: %s - %s",
                exc.response.status_code,
                exc.response.text,
            )
            raise ApiError(
                f"HTTP Error {exc.response.status_code}: {exc.response.text}"
            ) from exc
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
        """Retrieve probabilistic forecast for a latitude/longitude."""
        params = {
            "latitude": str(latitude),
            "longitude": str(longitude),
            "timesteps": timesteps,
            "excludeParameterMetadata": "FALSE",
            "includeLocationName": "TRUE",
        }
        try:
            return await self._make_request(self.base_url, params)
        except ApiError as err:
            _LOGGER.error("Point forecast request failed: %s", err)
            raise
