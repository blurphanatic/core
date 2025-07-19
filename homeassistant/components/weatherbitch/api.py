"""Met Office DataHub API client."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.httpx_client import AsyncClient

_LOGGER = logging.getLogger(__name__)


class ApiError(Exception):
    """Raised when the API client encounters an error."""


class MetOfficeApiClient:
    """Client for interacting with the Met Office DataHub point API."""

    def __init__(self, hass: HomeAssistant, api_key: str) -> None:
        """Initialize the client."""
        self.api_key = api_key
        self.base_url = "https://data.hub.api.metoffice.gov.uk/sitespecific/v0/point/"
        self.client = AsyncClient(hass=hass)

    def _get_headers(self) -> dict[str, str]:
        """Return headers for a request."""
        return {"apikey": self.api_key, "accept": "application/json"}

    async def _make_request(self, params: dict[str, Any]) -> dict[str, Any]:
        """Make a GET request to the API and return the JSON response."""
        try:
            response = await self.client.get(
                self.base_url, headers=self._get_headers(), params=params
            )
            response.raise_for_status()
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
        """Return the forecast for a specific coordinate."""
        params = {
            "latitude": str(latitude),
            "longitude": str(longitude),
            "timesteps": timesteps,
            "excludeParameterMetadata": "FALSE",
            "includeLocationName": "TRUE",
        }
        try:
            return await self._make_request(params)
        except ApiError as err:
            _LOGGER.error("Error fetching forecast: %s", err)
            raise
