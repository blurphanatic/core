"""Data coordinator for the Met Office integration."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import logging
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import BASE_URL, DEFAULT_SCAN_INTERVAL, VISIBILITY_MAP

_LOGGER = logging.getLogger(__name__)


class MetOfficeDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Met Office data."""

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        client_id: str,
        client_secret: str,
        site_id: str,
        site_name: str,
    ) -> None:
        """Initialize coordinator."""
        self.client_id = client_id
        self.client_secret = client_secret
        self.site_id = site_id
        self.site_name = site_name
        self.session = async_get_clientsession(hass)
        super().__init__(
            hass,
            _LOGGER,
            name=f"MetOffice Coordinator for {site_name}",
            update_interval=DEFAULT_SCAN_INTERVAL,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Met Office."""
        url = f"{BASE_URL}/all/json/{self.site_id}?res=hourly"
        headers = {
            "x-ibm-client-id": self.client_id,
            "x-ibm-client-secret": self.client_secret,
            "accept": "application/json",
        }
        _LOGGER.debug("Requesting %s", url)
        try:
            async with self.session.get(
                url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status != 200:
                    raise UpdateFailed(f"HTTP error: {resp.status}")
                data = await resp.json()
        except (TimeoutError, aiohttp.ClientError) as err:
            raise UpdateFailed(err) from err

        try:
            location = data.get("SiteRep", {}).get("DV", {}).get("Location")
            period = location.get("Period", [])[0]
            rep = period.get("Rep", [])[0]
        except (AttributeError, IndexError) as err:
            raise UpdateFailed("Unexpected response structure") from err

        date_str = period.get("value")
        minute_str = rep.get("$")
        if date_str is None or minute_str is None:
            raise UpdateFailed("Missing time information")

        try:
            base_date = datetime.strptime(date_str, "%Y-%m-%dZ")
            minutes = int(minute_str)
            timestamp = (base_date + timedelta(minutes=minutes)).replace(tzinfo=UTC)
        except ValueError as err:
            raise UpdateFailed("Invalid time data") from err

        def _to_float(value: Any) -> float | None:
            try:
                return float(value) if value is not None else None
            except (TypeError, ValueError):
                return None

        def _to_int(value: Any) -> int | None:
            try:
                return int(value) if value is not None else None
            except (TypeError, ValueError):
                return None

        def _mph_to_ms(value: Any) -> float | None:
            speed = _to_float(value)
            return round(speed * 0.44704, 2) if speed is not None else None

        visibility_code = rep.get("V")
        visibility = (
            VISIBILITY_MAP.get(visibility_code, "Unknown") if visibility_code else None
        )

        return {
            "time": timestamp,
            "wind_direction": rep.get("D"),
            "feels_like_temperature": _to_float(rep.get("F")),
            "wind_gust": _mph_to_ms(rep.get("G")),
            "humidity": _to_int(rep.get("H")),
            "precipitation_probability": _to_int(rep.get("P")),
            "wind_speed": _mph_to_ms(rep.get("S")),
            "temperature": _to_float(rep.get("T")),
            "visibility": visibility,
            "weather": _to_int(rep.get("W")),
            "uv_index": _to_int(rep.get("U")),
            "pressure": _to_float(rep.get("Pp")),
        }
