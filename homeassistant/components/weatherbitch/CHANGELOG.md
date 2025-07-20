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
## [0.1.8] - 2025-07-20
### Added
- All Met Office fields now mapped into Home Assistant forecast objects including dew point, min/max temperature, visibility, UV index, precipitation and snow amounts, and wind gust.
- Raw API data preserved under `raw` in each forecast.
### Changed
- `MetOfficeDataUpdateCoordinator` returns structured `{"current": ..., "forecast": [...]}`.
- Removed legacy `{"forecasts": ...}` output.
- `MetOfficeWeather` and sensors updated to consume new data structure.
### Fixed
- Consistent unit conversions for pressure.
### Findings/Deliverables Summary
- **Forecast Schema:** Expanded to include all API fields and raw payload.
- **Entities:** Simplified mapping via coordinator-provided data.
- **Testing:** Added unit test validating parsing and future filtering.

