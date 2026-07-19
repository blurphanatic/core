"""The Met Office integration."""

# pylint: disable=hass-enforce-class-module

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ApiError, MetOfficeApiClient
from .const import (
    API_CALL_COUNTER_KEY,
    CONF_API_KEY,
    CONF_TIMESTEPS,
    CONF_UPDATE_INTERVAL,
    DOMAIN,
    FORECAST_TYPE_DAILY,
    FORECAST_TYPE_HOURLY,
    FORECAST_TYPE_TWICE_DAILY,
    FIELD_DAY_MAX_TEMP,
    FIELD_NIGHT_MIN_TEMP,
    FIELD_DAY_WEATHER_CODE,
    FIELD_NIGHT_WEATHER_CODE,
    FIELD_DAY_PRECIP_PROB,
    FIELD_NIGHT_PRECIP_PROB,
    FIELD_DAY_MAX_FEELS_LIKE,
    FIELD_NIGHT_MIN_FEELS_LIKE,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.WEATHER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Met Office entry."""
    api_key = entry.data[CONF_API_KEY]
    latitude = entry.data[CONF_LATITUDE]
    longitude = entry.data[CONF_LONGITUDE]

    # Read from options first, then data (for backward compatibility with existing entries)
    timesteps = entry.options.get(
        CONF_TIMESTEPS,
        entry.data.get(CONF_TIMESTEPS, "hourly"),
    )
    update_interval_minutes = entry.options.get(
        CONF_UPDATE_INTERVAL,
        entry.data.get(CONF_UPDATE_INTERVAL, 15),
    )
    update_interval_td = timedelta(minutes=update_interval_minutes)

    client = MetOfficeApiClient(hass, api_key)
    coordinator = MetOfficeDataUpdateCoordinator(
        hass, client, latitude, longitude, timesteps, update_interval_td, entry
    )

    hass.data.setdefault(DOMAIN, {})
    if API_CALL_COUNTER_KEY not in hass.data[DOMAIN]:
        hass.data[DOMAIN][API_CALL_COUNTER_KEY] = {
            "count": 0,
            "last_reset_date": datetime.now(UTC).date(),
        }

    hass.data[DOMAIN][entry.entry_id] = coordinator
    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener for options changes
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update by reloading the integration."""
    _LOGGER.info("Options updated for %s, reloading integration", entry.title)
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


def get_device_info(latitude: float, longitude: float, name: str) -> DeviceInfo:
    """Return device registry information."""
    return DeviceInfo(
        entry_type=dr.DeviceEntryType.SERVICE,
        identifiers={(DOMAIN, f"{latitude},{longitude}")},
        manufacturer="Met Office",
        name=f"Met Office {name}",
    )


class MetOfficeDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to fetch data from the Met Office API.

    This coordinator fetches ALL forecast types (hourly and daily) in parallel
    and provides them in a unified data structure. It also derives twice-daily
    forecasts from daily data by splitting day/night entries.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        client: MetOfficeApiClient,
        latitude: float,
        longitude: float,
        timesteps: str,
        update_interval_td: timedelta,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance.
            client: API client used to retrieve forecasts.
            latitude: Latitude of forecast location.
            longitude: Longitude of forecast location.
            timesteps: Legacy timesteps parameter (kept for backward compatibility).
            update_interval_td: Update interval for coordinator.
            config_entry: Config entry associated with this coordinator.
        """
        self.client = client
        self.latitude = latitude
        self.longitude = longitude
        self.timesteps = timesteps  # Kept for backward compatibility
        self.config_entry: ConfigEntry = config_entry
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval_td)
        self.data: dict[str, Any] = {}

    def _extract_time_series(self, api_response: dict[str, Any], forecast_type: str) -> list[dict[str, Any]]:
        """Extract and validate timeSeries from API response.

        Args:
            api_response: Raw API response dictionary.
            forecast_type: Type of forecast for logging purposes.

        Returns:
            List of time series entries.

        Raises:
            UpdateFailed: If required data is missing from the response.
        """
        features = api_response.get("features")
        if not isinstance(features, list) or not features:
            _LOGGER.warning(
                "%s API response 'features' list missing or empty: %s",
                forecast_type,
                features,
            )
            raise UpdateFailed(f"Missing features in {forecast_type} API response")

        properties = features[0].get("properties")
        if not isinstance(properties, dict):
            _LOGGER.warning(
                "%s API response 'properties' missing or not a dict: %s",
                forecast_type,
                properties,
            )
            raise UpdateFailed(f"Missing properties in {forecast_type} API response")

        time_series = properties.get("timeSeries")
        if not isinstance(time_series, list) or not time_series:
            _LOGGER.warning(
                "%s API response 'timeSeries' list missing or empty: %s",
                forecast_type,
                time_series,
            )
            raise UpdateFailed(f"Missing timeSeries in {forecast_type} API response")

        return time_series

    def _process_hourly_forecast(self, forecast_item: dict[str, Any]) -> dict[str, Any]:
        """Process a single hourly forecast entry.

        Performs unit conversion and key normalization for hourly data.

        Args:
            forecast_item: Raw forecast entry from the API.

        Returns:
            Processed forecast entry with unified keys.
        """
        processed = forecast_item.copy()

        # Convert mslp from Pascals (Pa) to hectoPascals (hPa)
        mslp_pa = processed.get("mslp")
        if mslp_pa is not None:
            processed["mslp"] = mslp_pa / 100.0

        # Unify feelsLikeTemperature key (hourly uses 'feelsLikeTemperature',
        # three-hourly uses 'feelsLikeTemp')
        if "feelsLikeTemp" in processed and "feelsLikeTemperature" not in processed:
            processed["feelsLikeTemperature"] = processed["feelsLikeTemp"]

        # Unify temperature keys for three-hourly data
        if "screenTemperature" not in processed:
            min_temp = processed.get("minScreenAirTemp")
            max_temp = processed.get("maxScreenAirTemp")
            if min_temp is not None and max_temp is not None:
                processed["screenTemperature"] = (min_temp + max_temp) / 2.0

        # Unify wind gust keys (three-hourly uses max10mWindGust)
        if "windGust10m" not in processed:
            max_gust = processed.get("max10mWindGust")
            if max_gust is not None:
                processed["windGust10m"] = max_gust

        return processed

    def _process_daily_forecast(self, forecast_item: dict[str, Any]) -> dict[str, Any]:
        """Process a single daily forecast entry.

        Creates a daily forecast with temp_high and temp_low properly separated,
        and adds unified keys for backward compatibility.

        Args:
            forecast_item: Raw daily forecast entry from the API.

        Returns:
            Processed daily forecast entry with temp_high/temp_low and unified keys.
        """
        processed = forecast_item.copy()

        # Extract day max and night min as temp_high and temp_low
        day_max = processed.get(FIELD_DAY_MAX_TEMP)
        night_min = processed.get(FIELD_NIGHT_MIN_TEMP)

        if day_max is not None:
            processed["temp_high"] = day_max
        if night_min is not None:
            processed["temp_low"] = night_min

        # For backward compatibility: set screenTemperature as average
        if day_max is not None and night_min is not None:
            processed["screenTemperature"] = (day_max + night_min) / 2.0

        # Feels like temperature
        day_max_feels = processed.get(FIELD_DAY_MAX_FEELS_LIKE)
        night_min_feels = processed.get(FIELD_NIGHT_MIN_FEELS_LIKE)
        if day_max_feels is not None and night_min_feels is not None:
            processed["feelsLikeTemperature"] = (day_max_feels + night_min_feels) / 2.0

        # Convert pressure (midday value)
        midday_mslp = processed.get("middayMslp")
        if midday_mslp is not None:
            processed["mslp"] = midday_mslp / 100.0

        # Map day-specific fields to unified names
        if FIELD_DAY_WEATHER_CODE in processed:
            processed["significantWeatherCode"] = processed[FIELD_DAY_WEATHER_CODE]

        if FIELD_DAY_PRECIP_PROB in processed:
            processed["probOfPrecipitation"] = processed[FIELD_DAY_PRECIP_PROB]

        # Wind data (midday values)
        if "midday10MWindSpeed" in processed:
            processed["windSpeed10m"] = processed["midday10MWindSpeed"]
        if "midday10MWindDirection" in processed:
            processed["windDirectionFrom10m"] = processed["midday10MWindDirection"]
        if "midday10MWindGust" in processed:
            processed["windGust10m"] = processed["midday10MWindGust"]

        # Other midday values
        if "middayVisibility" in processed:
            processed["visibility"] = processed["middayVisibility"]
        if "middayRelativeHumidity" in processed:
            processed["screenRelativeHumidity"] = processed["middayRelativeHumidity"]
        if "maxUvIndex" in processed:
            processed["uvIndex"] = processed["maxUvIndex"]

        return processed

    def _build_twice_daily_forecasts(
        self, daily_forecasts: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Build twice-daily forecasts from daily data.

        Creates TWO entries per daily entry:
        1. Day entry (is_daytime=True) using day* fields
        2. Night entry (is_daytime=False) using night* fields

        Args:
            daily_forecasts: List of processed daily forecast entries.

        Returns:
            List of twice-daily forecast entries.
        """
        twice_daily = []

        for daily_entry in daily_forecasts:
            time_str = daily_entry.get("time", "")

            # Day entry
            day_entry = {
                "time": time_str,
                "is_daytime": True,
                "temperature": daily_entry.get(FIELD_DAY_MAX_TEMP),
                "feels_like": daily_entry.get(FIELD_DAY_MAX_FEELS_LIKE),
                "precipitation_probability": daily_entry.get(FIELD_DAY_PRECIP_PROB),
                "weather_code": daily_entry.get(FIELD_DAY_WEATHER_CODE),
                # Include original fields for compatibility
                "significantWeatherCode": daily_entry.get(FIELD_DAY_WEATHER_CODE),
                "screenTemperature": daily_entry.get(FIELD_DAY_MAX_TEMP),
                "feelsLikeTemperature": daily_entry.get(FIELD_DAY_MAX_FEELS_LIKE),
                "probOfPrecipitation": daily_entry.get(FIELD_DAY_PRECIP_PROB),
                # Wind data (use midday values for day)
                "windSpeed10m": daily_entry.get("midday10MWindSpeed"),
                "windDirectionFrom10m": daily_entry.get("midday10MWindDirection"),
                "windGust10m": daily_entry.get("midday10MWindGust"),
                # UV index (day only)
                "uvIndex": daily_entry.get("maxUvIndex"),
                # Visibility and humidity (midday)
                "visibility": daily_entry.get("middayVisibility"),
                "screenRelativeHumidity": daily_entry.get("middayRelativeHumidity"),
                # Pressure (midday, already converted if present)
                "mslp": daily_entry.get("mslp"),
            }

            # Night entry
            night_entry = {
                "time": time_str,
                "is_daytime": False,
                "temperature": daily_entry.get(FIELD_NIGHT_MIN_TEMP),
                "feels_like": daily_entry.get(FIELD_NIGHT_MIN_FEELS_LIKE),
                "precipitation_probability": daily_entry.get(FIELD_NIGHT_PRECIP_PROB),
                "weather_code": daily_entry.get(FIELD_NIGHT_WEATHER_CODE),
                # Include original fields for compatibility
                "significantWeatherCode": daily_entry.get(FIELD_NIGHT_WEATHER_CODE),
                "screenTemperature": daily_entry.get(FIELD_NIGHT_MIN_TEMP),
                "feelsLikeTemperature": daily_entry.get(FIELD_NIGHT_MIN_FEELS_LIKE),
                "probOfPrecipitation": daily_entry.get(FIELD_NIGHT_PRECIP_PROB),
                # Wind data (use midnight values for night)
                "windSpeed10m": daily_entry.get("midnight10MWindSpeed"),
                "windDirectionFrom10m": daily_entry.get("midnight10MWindDirection"),
                "windGust10m": daily_entry.get("midnight10MWindGust"),
                # UV index not applicable for night
                "uvIndex": 0,
                # Visibility and humidity (midnight)
                "visibility": daily_entry.get("midnightVisibility"),
                "screenRelativeHumidity": daily_entry.get("midnightRelativeHumidity"),
                # Pressure (midnight)
                "mslp": (
                    daily_entry.get("midnightMslp", 0) / 100.0
                    if daily_entry.get("midnightMslp") is not None
                    else daily_entry.get("mslp")
                ),
            }

            twice_daily.append(day_entry)
            twice_daily.append(night_entry)

        _LOGGER.debug(
            "Built %d twice-daily entries from %d daily forecasts",
            len(twice_daily),
            len(daily_forecasts),
        )

        return twice_daily

    def _validate_forecast_keys(
        self, forecasts: list[dict[str, Any]], forecast_type: str
    ) -> None:
        """Validate expected keys in forecast entries.

        Args:
            forecasts: List of processed forecast entries.
            forecast_type: Type of forecast for logging.
        """
        if not forecasts:
            return

        expected_keys = {
            "time",
            "screenTemperature",
            "feelsLikeTemperature",
            "probOfPrecipitation",
            "windDirectionFrom10m",
            "windSpeed10m",
            "windGust10m",
            "screenRelativeHumidity",
            "mslp",
            "uvIndex",
            "visibility",
            "significantWeatherCode",
        }

        missing = [key for key in expected_keys if key not in forecasts[0]]
        if missing:
            _LOGGER.warning(
                "Missing expected %s forecast keys in first entry: %s",
                forecast_type,
                missing,
            )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch latest data from Met Office.

        Fetches both hourly and daily forecasts in parallel, processes them,
        and builds a unified data structure including twice-daily forecasts.

        Returns:
            Dictionary containing:
                - 'current': First hourly entry for current conditions
                - 'hourly': List of processed hourly forecasts
                - 'daily': List of processed daily forecasts with temp_high/temp_low
                - 'twice_daily': List of day/night entries derived from daily
                - 'forecasts': Alias to hourly for backward compatibility
        """
        try:
            # Fetch all forecasts (hourly and daily) in parallel
            all_data = await self.client.get_all_forecasts(
                self.latitude, self.longitude
            )

            # --- API Call Counter Logic ---
            api_counter = self.hass.data[DOMAIN][API_CALL_COUNTER_KEY]
            current_date = datetime.now(UTC).date()
            if current_date != api_counter["last_reset_date"]:
                api_counter["count"] = 0
                api_counter["last_reset_date"] = current_date
            # Count 2 API calls (hourly + daily)
            api_counter["count"] += 2
            _LOGGER.info(
                "Met Office API calls successful for %s. Total calls today: %d",
                self.config_entry.title,
                api_counter["count"],
            )

        except ApiError as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err

        # Extract time series from both responses
        hourly_series = self._extract_time_series(
            all_data[FORECAST_TYPE_HOURLY], FORECAST_TYPE_HOURLY
        )
        daily_series = self._extract_time_series(
            all_data[FORECAST_TYPE_DAILY], FORECAST_TYPE_DAILY
        )

        # Filter daily to entries with valid day data
        daily_series = [
            entry for entry in daily_series if FIELD_DAY_WEATHER_CODE in entry
        ]
        if not daily_series:
            _LOGGER.warning("No daily forecast entries with day data found")
            # Continue without daily data rather than failing completely

        # Process hourly forecasts
        processed_hourly = [
            self._process_hourly_forecast(entry) for entry in hourly_series
        ]

        # Process daily forecasts
        processed_daily = [
            self._process_daily_forecast(entry) for entry in daily_series
        ]

        # Build twice-daily from daily data
        twice_daily = self._build_twice_daily_forecasts(daily_series)

        # Validate processed data
        self._validate_forecast_keys(processed_hourly, FORECAST_TYPE_HOURLY)
        self._validate_forecast_keys(processed_daily, FORECAST_TYPE_DAILY)

        # Build current conditions from first hourly entry
        current = processed_hourly[0] if processed_hourly else {}

        _LOGGER.debug(
            "Processed forecasts: hourly=%d, daily=%d, twice_daily=%d",
            len(processed_hourly),
            len(processed_daily),
            len(twice_daily),
        )

        # Return unified data structure
        return {
            "current": current,
            FORECAST_TYPE_HOURLY: processed_hourly,
            FORECAST_TYPE_DAILY: processed_daily,
            FORECAST_TYPE_TWICE_DAILY: twice_daily,
            # Backward compatibility: 'forecasts' points to hourly data
            "forecasts": processed_hourly,
        }
