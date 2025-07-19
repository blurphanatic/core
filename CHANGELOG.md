## [0.1.0] - 2025-07-19
### Added
- Implemented `MetOfficeApiClient` for point-based forecast retrieval using API key authentication.
- Added new configuration flow prompting for API key, latitude, longitude, and entry name.
- Created `MetOfficeDataUpdateCoordinator` for periodic data fetching.
- Introduced sensor and weather entities using new forecast fields.
### Changed
- Updated manifest domain to `metoffice` and refactored constants.
### Fixed
- N/A
### Findings/Deliverables Summary
- **API Client:** Added robust `_make_request` with error handling and point forecast method.
- **Config Flow:** Simplified user step with inline API key validation.
- **Data Coordinator:** Fetches full forecast via `get_point_forecast` and handles empty data.
- **Entities:** Sensors expose temperature, humidity, wind, and other metrics; weather entity maps `significantWeatherCode` using `METOFFICE_WEATHER_CODE_MAP`.
- **Robustness:** All JSON access via `.get()` with defaults; network and HTTP errors logged via `_LOGGER`.
- **Ambiguity Resolutions:** Forecast list assumed under `forecasts`; weather entity returns full list for HA forecast property.

