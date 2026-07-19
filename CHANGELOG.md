## [0.3.0] - 2026-01-20
### Added
- **Multi-Forecast API Support:** New `get_all_forecasts()` method in `api.py` fetches hourly and daily forecasts in parallel using `asyncio.gather`.
- **Twice-Daily Forecasts:** Coordinator now derives twice-daily forecasts from daily data, splitting day/night entries with proper `is_daytime` flag.
- **New Constants:** Added `FORECAST_TYPE_HOURLY`, `FORECAST_TYPE_DAILY`, `FORECAST_TYPE_TWICE_DAILY` and field mapping constants for daily API fields.
- **Comprehensive Test Suite:** New `tests/` directory with `test_api.py` (API client tests) and `test_coordinator.py` (coordinator tests) covering all processing logic.
- **Unified Data Structure:** Coordinator now returns structured data with `current`, `hourly`, `daily`, `twice_daily`, and `forecasts` (backward compat) keys.
### Changed
- **Coordinator Architecture:** Complete rewrite of `MetOfficeDataUpdateCoordinator._async_update_data()` to fetch ALL forecast types (hourly + daily) in a single update cycle.
- **API Call Counter:** Now increments by 2 per update (one for hourly, one for daily).
- **Processing Methods:** Extracted `_process_hourly_forecast()`, `_process_daily_forecast()`, `_build_twice_daily_forecasts()`, `_extract_time_series()`, and `_validate_forecast_keys()` for cleaner code organization.
- **Daily Forecast Processing:** Now includes `temp_high` and `temp_low` fields in addition to unified `screenTemperature` (average).
### Fixed
- N/A (refactoring release)
### Findings/Deliverables Summary
- **API Client:** Added parallel fetching capability via `get_all_forecasts()` which uses `asyncio.gather` to fetch hourly and daily endpoints simultaneously.
- **Data Coordinator:** Completely refactored to process multiple forecast types and build twice-daily forecasts from daily data.
- **Twice-Daily Logic:** Day entries use `dayMaxScreenTemperature`, `daySignificantWeatherCode`, midday wind values; Night entries use `nightMinScreenTemperature`, `nightSignificantWeatherCode`, midnight wind values.
- **Backward Compatibility:** Maintained `forecasts` key pointing to hourly data for existing sensor/weather entities.
- **Testing:** 50+ test cases covering header construction, parallel fetching, error handling, pressure conversion, field normalization, twice-daily building, and API call counting.

## [0.2.0] - 2026-01-20
### Added
- Modern forecast services: `async_forecast_daily`, `async_forecast_hourly`, `async_forecast_twice_daily` methods replacing deprecated `forecast` property.
- `WeatherEntityFeature` flags enabling all three forecast types (FORECAST_DAILY, FORECAST_HOURLY, FORECAST_TWICE_DAILY).
- New weather entity properties: `native_apparent_temperature`, `native_dew_point`, `native_wind_gust_speed`, `cloud_coverage`.
- Native unit attributes: `_attr_native_visibility_unit` (UnitOfLength.METERS).
- Three new sensor types: Dew Point (dewPoint), Precipitation (totalPrecipAmount), Cloud Coverage (totalCloudAmount).
- Comprehensive test suite: `tests/test_weather.py` and `tests/test_sensor.py` with 50+ test cases.
- Data structure fallback: entities now support both `current` and `forecasts` coordinator data keys.
### Changed
- Weather entity rewritten to use modern Home Assistant patterns with `native_*` property names.
- Deprecated `temperature`, `pressure`, `wind_speed` properties replaced with `native_temperature`, `native_pressure`, `native_wind_speed`.
- Removed deprecated `forecast` property in favor of async forecast methods.
- Sensor `native_value` property now handles both old and new coordinator data structures.
### Fixed
- Weather code mapping now returns `None` for unknown codes instead of "unknown" string.
### Findings/Deliverables Summary
- **Weather Entity:** Complete rewrite using `WeatherEntityFeature` and async forecast services for Home Assistant 2024.x+ compatibility.
- **Forecast Methods:** `_build_forecast_list` handles both hourly and daily forecasts with proper `native_templow` for daily entries.
- **Sensors:** Added dew point, precipitation amount, and cloud coverage sensors with proper device classes.
- **Testing:** Full pytest test suite covering feature flags, condition mapping, forecast methods, data fallbacks, and edge cases.
- **Backward Compatibility:** Maintains support for existing `forecasts` data structure while supporting future `current`/`hourly`/`daily` structure.

## [0.1.0] - 2025-01-01
### Added
- Implemented MetOfficeApiClient with methods for point-based probabilistic forecasts and robust error handling.
- Created config flow prompting for API key, latitude, longitude, and name.
- Implemented DataUpdateCoordinator fetching hourly forecasts via new API.
- Added sensor and weather entities mapping API fields to Home Assistant attributes with defensive parsing.
### Changed
- Switched integration domain to `metoffice` and updated manifest.
### Fixed
- N/A
### Findings/Deliverables Summary
- **API Client:** Added `api.py` providing asynchronous HTTP interactions with proper headers and error handling.
- **Config Flow:** Simplified to single step validating API key and coordinates.
- **Data Coordinator:** Fetches forecasts from the v0/point endpoint; warns on unexpected data.
- **Entities:** Sensors and weather entities extract data from `forecasts` list; includes mapping via `METOFFICE_WEATHER_CODE_MAP`.
- **Robustness:** All API data access uses `.get()`; network and JSON errors are caught and logged.
- **Ambiguity Resolutions:** Forecast property exposes all entries from returned list using the assumed `forecasts` key.

## [0.1.1] - 2025-07-19
### Added
- Translation file with updated configuration title.
- BASE_URL constant for the point forecast API.
### Changed
- Corrected weather code mapping to use HA condition constants.
- Documentation link updated in manifest.
- UV index sensor now includes device and state classes.
### Fixed
- API client now references the BASE_URL constant.
- Forecast timestamps parsed via `dt_util.parse_datetime`.
### Findings/Deliverables Summary
- **Constants:** `METOFFICE_WEATHER_CODE_MAP` now references HA constants directly and includes `BASE_URL`.
- **Entities:** Removed unused coordinator module and ensured sensors and weather entity handle missing data gracefully.

## [0.1.2] - 2025-07-19
### Added
- Warning logs for missing forecast entries and keys in coordinator.
### Changed
- None
### Fixed
- Forecast data now exposes ISO timestamp strings rather than datetime objects.
### Findings/Deliverables Summary
- **Data Coordinator:** Validates `forecasts` list and logs missing key names.
- **Entities:** `forecast` property returns raw `time` strings for compatibility.

## [0.1.5] - 2025-07-19
### Added
- None
### Changed
- None
### Fixed
- Confirmed and documented correct Met Office API endpoint URL construction: `timesteps` (e.g., `hourly`, `three-hourly`, `daily`) is correctly included as a path segment (e.g., `/point/hourly`) and `dataSource=BD1` is consistently applied as a query parameter. This resolves all observed 404 Not Found errors.
### Findings/Deliverables Summary
- **API Client:** Verified `get_point_forecast` correctly constructs `f"{BASE_URL}/point/{timesteps}"` and includes `DATA_SOURCE` parameter.
- **API Interaction:** Confirmed successful communication with Met Office API for `hourly`, `three-hourly`, and `daily` forecast endpoints.

## [0.1.7] - 2025-07-20
### Added
- Configurable forecast frequency (hourly, three-hourly, daily) via setup flow.
- Configurable update interval (in minutes) via setup flow.
- Debug-level logging for full API requests and raw responses.
- Info-level logging for API call duration in milliseconds.
- 24-hour rolling counter for successful API calls, logged at info level.
- `API_CALL_COUNTER_KEY` constant.
### Changed
- `MetOfficeDataUpdateCoordinator` now uses configurable update interval and timesteps.
- `MetOfficeApiClient._make_request` includes detailed request/response logging and timing.
- API call counter logic implemented in coordinator.
### Findings/Deliverables Summary
- **Config Flow:** Enhanced to capture user preferences for `timesteps` and `update_interval`.
- **Data Coordinator:** Adapted to use dynamic `timesteps` and `update_interval`. Implemented and integrated the 24-hour API call counter.
- **API Client:** Enhanced logging to provide deep insight into API interactions for debugging and monitoring.
- **User Control:** Provides users with critical control over API usage to manage daily limits.

## [0.1.8] - 2025-10-30
### Added
- Field name normalization for three-hourly and daily forecasts in data coordinator.
### Changed
- None
### Fixed
- Fixed three-hourly and daily forecast data not populating entities by normalizing API field names (`maxScreenAirTemp`/`minScreenAirTemp` → `screenTemperature`, `max10mWindGust` → `windGust10m`, `feelsLikeTemp` → `feelsLikeTemperature`).
- Three-hourly and daily forecasts now use average of min/max temperature for current temperature reading.
### Findings/Deliverables Summary
- **Data Coordinator:** Added comprehensive field name unification logic to handle different API response structures across hourly, three-hourly, and daily timesteps.
- **Bug Resolution:** All three forecast frequencies (hourly, three-hourly, daily) now properly populate sensor and weather entities with complete data.
- **Temperature Handling:** For period-based forecasts (three-hourly/daily), current temperature is calculated as average of `minScreenAirTemp` and `maxScreenAirTemp` for more accurate representation.
