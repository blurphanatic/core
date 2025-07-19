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
