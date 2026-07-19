# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a **custom Home Assistant integration** for the UK Met Office DataHub API, providing point-based probabilistic weather forecasts. The integration is branded as "Weather Bitch" (domain: `weatherbitch`) and delivers site-specific forecasts using latitude/longitude coordinates.

**Critical Context**: This integration is part of a larger Home Assistant production configuration at `/home/mike/homeassistant/config/` but lives independently in `custom_components/weatherbitch/` as a standalone integration with its own git repository (https://github.com/blurphanatic/core.git).

## Development Philosophy

This project follows **strict engineering discipline** governed by `AGENTS.md` - the supreme governing document that outlines non-negotiable protocols. Read it before making any changes.

### Core Mandates from AGENTS.md

1. **Authentication**: ONLY use `apikey` header (lowercase) with `Accept: application/json`. NO IBM headers, OAuth, or other methods.
2. **Changelog Discipline**: Every commit MUST have a detailed, timestamped entry in `CHANGELOG.md` following the established format.
3. **Logging**: Comprehensive logging is mandatory for all API interactions, errors, and data processing.
4. **Code Quality**: All classes/methods require docstrings; defensive programming is prioritized.
5. **Versioning**: Strict Semantic Versioning (SemVer: MAJOR.MINOR.PATCH).

## Architecture

### Component Structure

```
weatherbitch/
├── __init__.py          # Entry point, DataUpdateCoordinator setup
├── api.py               # Met Office DataHub API client (httpx-based)
├── config_flow.py       # User setup flow for API key, location, preferences
├── const.py             # Constants, weather code mappings
├── sensor.py            # Individual weather sensors (temperature, humidity, etc.)
├── weather.py           # Weather entity with forecast data
├── helpers.py           # Legacy helpers (NOT actively used)
├── coordinator.py       # Deprecated (logic moved to __init__.py)
├── manifest.json        # Integration metadata
└── strings.json         # UI strings for config flow
```

### Key Architecture Patterns

**DataUpdateCoordinator Pattern**: The `MetOfficeDataUpdateCoordinator` in `__init__.py` handles:
- Periodic API fetching based on user-configured interval (15 min to 6 hours)
- Data processing and unit conversion (Pa → hPa for pressure)
- Key unification (`feelsLikeTemp` → `feelsLikeTemperature`)
- API call counting (resets daily at midnight UTC)

**Point-Based API**: Uses latitude/longitude with configurable timesteps:
- `hourly`: Hourly forecasts
- `three-hourly`: 3-hour intervals
- `daily`: Daily forecasts

**API Endpoint Construction**:
```python
f"{BASE_URL}/point/{timesteps}?latitude={lat}&longitude={lon}&dataSource=BD1"
```

### Data Flow

1. User configures via `ConfigFlow` → stores API key, coordinates, timesteps, update interval
2. `async_setup_entry` creates `MetOfficeDataUpdateCoordinator` → spawns `MetOfficeApiClient`
3. Coordinator fetches from API → processes `timeSeries` array → returns `{"forecasts": [...]}`
4. Sensor/Weather entities read from `coordinator.data["forecasts"][0]` (current conditions)
5. Weather entity's `forecast` property exposes full forecast array

## Common Development Tasks

### Testing Configuration Changes

Home Assistant must reload the integration after code changes:

```bash
# From Home Assistant host or container
ha core restart

# Check logs for errors
ha core logs
```

### Checking API Responses

The integration logs full API requests/responses at DEBUG level. To enable in Home Assistant:

```yaml
# In configuration.yaml
logger:
  logs:
    custom_components.weatherbitch: debug
```

### Version Bumps

When changing version:
1. Update `manifest.json` version field
2. Add changelog entry with version header: `## [X.Y.Z] - YYYY-MM-DD`
3. Commit with semantic prefix: `feat:`, `fix:`, `chore:`

### Understanding API Call Limits

The Met Office API has daily call limits. The integration tracks calls via:
- `API_CALL_COUNTER_KEY` in `hass.data[DOMAIN]`
- Counter resets at midnight UTC
- Logged at INFO level: `"Total calls today: N"`

Users control API usage via update interval configuration (default: 15 minutes).

## Critical Constants

### API Configuration (const.py)
- `BASE_URL`: `https://data.hub.api.metoffice.gov.uk/sitespecific/v0`
- `DATA_SOURCE`: `"BD1"` (mandatory query parameter)
- `DOMAIN`: `"weatherbitch"` (integration identifier)

### Weather Code Mapping
`METOFFICE_WEATHER_CODE_MAP` maps Met Office significant weather codes (0-30) to Home Assistant conditions:
- 0: Clear night
- 1: Sunny
- 5-6: Fog
- 9-15: Rainy (various intensities)
- 16-27: Snowy/hail
- 28-30: Lightning/thunderstorm

## Data Processing Quirks

### Unit Conversions
The coordinator automatically converts:
- **Pressure**: API returns Pascals (Pa) → converted to hectoPascals (hPa) by dividing by 100

### Key Unification
API responses vary by timestep:
- `hourly` uses `feelsLikeTemperature`
- `three-hourly`/`daily` use `feelsLikeTemp`

The coordinator unifies to `feelsLikeTemperature` for consistency.

### Expected Forecast Fields
Each forecast item should contain:
- `time` (ISO timestamp)
- `screenTemperature`, `feelsLikeTemperature`
- `probOfPrecipitation`, `windDirectionFrom10m`, `windSpeed10m`, `windGust10m`
- `screenRelativeHumidity`, `mslp`, `uvIndex`, `visibility`
- `significantWeatherCode`

Missing fields trigger WARNING logs but don't fail the update (graceful degradation).

## Error Handling Patterns

### API Client (api.py)
- `httpx.HTTPStatusError` with 401 → raises `ConfigEntryAuthFailed` (triggers reauth flow)
- Other HTTP errors → raises `ApiError` with status code and response body
- `httpx.RequestError` → raises `ApiError` for network issues
- `json.JSONDecodeError` → raises `ApiError` for malformed responses

### Coordinator (__init__.py)
- `ApiError` → wrapped in `UpdateFailed` exception
- Missing/empty `features`, `properties`, or `timeSeries` → logs WARNING and raises `UpdateFailed`

### Entities (sensor.py, weather.py)
- Use `.get()` with defaults to handle missing keys gracefully
- Empty data returns `None` for sensor states

## Home Assistant Integration Guidelines

This integration follows Home Assistant best practices:
- **Async/await**: All I/O operations are asynchronous
- **httpx client**: Uses `get_async_client(hass)` for HTTP requests
- **Device Registry**: Uses `DeviceInfo` with `entry_type=SERVICE`
- **Config Entry**: Supports GUI configuration flow (no YAML config)
- **Platforms**: Implements `sensor` and `weather` platforms

## Known Legacy Code

- `helpers.py`: Contains old Datapoint API code using the deprecated `datapoint` library. **NOT actively used** by current implementation.
- `coordinator.py`: Deprecated coordinator implementation. Logic moved to `__init__.py`.

These files remain for historical reference but should not be modified.

## Git Workflow

Development follows conventional commits:
- `feat:` for new features (MINOR version bump)
- `fix:` for bug fixes (PATCH version bump)
- `chore:` for maintenance tasks

Recent history shows Home Assistant compatibility updates focused on API migration from legacy Datapoint to DataHub API.
