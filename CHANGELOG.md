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
