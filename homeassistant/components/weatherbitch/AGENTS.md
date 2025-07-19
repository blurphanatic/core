AGENTS.MD - MET OFFICE INTEGRATION DIRECTIVE
DOCUMENT PURPOSE: This is the supreme governing document for the Met Office Home Assistant Integration. It outlines the project's mission, the critical technical mandates, and the NON-NEGOTIABLE PROTOCOLS for all development agents, human or AI. Adherence is mandatory. This document supersedes all previous instructions.
1.0 MISSION STATEMENT
To engineer, deploy, and maintain the most robust, accurate, and user-friendly Met Office DataHub integration for Home Assistant. This integration will serve as a benchmark for external API consumption within the Home Assistant ecosystem, delivering precise, site-specific probabilistic forecasts. We are not building a simple connector; we are forging a foundational weather data asset for Home Assistant users.
2.0 ARCHITECTURAL DECREE (CONTEXT)
The integration's architecture is established within the Home Assistant framework. All development will adhere to this stack and its principles:
* Framework: Home Assistant Integration (Python)
* API Client: Dedicated, robust httpx-based client for Met Office DataHub.
* Data Flow: DataUpdateCoordinator for periodic fetching and state management.
* User Configuration: ConfigFlow for secure and guided setup.
* Entities: Standard Home Assistant SensorEntity and WeatherEntity types.
3.0 OPERATIONAL PROTOCOLS (NON-NEGOTIABLE)
DEVIATION FROM THESE PROTOCOLS IS A CRITICAL FAILURE. NO EXCUSES, CODING BITCHES.
3.1 Authentication Mechanism Mandate
* THE LAW: The ONLY accepted authentication method is the apikey HTTP request header.
* THE MANDATE:
   * Header Key: apikey (lowercase, exactly as specified).
   * Value: The user-provided Met Office DataHub API key.
   * ADDITIONAL REQUIRED HEADER: Accept: application/json for all API requests.
* FORBIDDEN METHODS:
   * NO x-ibm-client-id or any other IBM-specific headers.
   * NO OAuth, NO client secrets, NO client IDs in the request body or query parameters.
   * NO hardcoding of API keys.
* STRICT ADHERENCE: The authentication mechanism MUST precisely match the apikey: <YOUR-API-KEY> header-only method documented in the Met Office DataHub API docs.
3.2 Robust Logging Discipline
* THE LAW: Comprehensive and context-rich logging is mandatory.
* THE MANDATE:
   * Use _LOGGER (from logging).
   * API Interactions: Log every significant API request and its outcome (success, failure).
   * Error Logging:
      * Log all httpx.RequestError (network issues) as ERROR.
      * Log all httpx.HTTPStatusError (non-200 HTTP responses) as ERROR, including the status code and response body.
      * Log json.JSONDecodeError as ERROR if API responses are malformed.
      * Log UpdateFailed exceptions in the Data Coordinator with descriptive messages.
   * Data Processing: Log WARNING if expected data fields (e.g., timeSeries, specific forecast properties) are missing from a valid API response, indicating graceful degradation.
   * Authentication Failures: Log ERROR when ConfigEntryAuthFailed occurs.
   * Informative Messages: Log messages MUST be clear, concise, and provide enough context for debugging (e.g., endpoint, error type, relevant data snippets).
3.3 Changelog Discipline (Redux)
* THE LAW: The CHANGELOG.md file in the root directory is the single, immutable source of truth for ALL changes.
* THE MANDATE: Every single commit that alters code, functionality, or dependencies MUST have a corresponding, DETAILED, TIMESTAMPED ENTRY in the changelog.
* FORMATTING: All entries MUST strictly adhere to the following format, appending to the existing changelog:
## [VERSION] - YYYY-MM-DD
### Added
- For new features introduced (e.g., "Implemented MetOfficeApiClient with methods for collections, locations, and site forecasts.").
### Changed
- For modifications to existing functionality (e.g., "Refactored ConfigFlow to include location selection step.").
### Fixed
- For any bug fixes (e.g., "Resolved issue where missing 'uvIndex' field caused sensor to fail.").
### Findings/Deliverables Summary
- **API Client:** Detailed summary of `api.py` methods implemented and their error handling.
- **Config Flow:** Detailed summary of `config_flow.py` steps, input validation, and data storage.
- **Data Coordinator:** Detailed summary of `__init__.py` coordinator setup, update logic, and data extraction (e.g., "Extracting first `timeSeries` entry as current forecast.").
- **Entities:** Detailed summary of `sensor.py` and `weather.py` entities, including specific fields mapped and the `METOFFICE_WEATHER_CODE_MAP` implementation.
- **Robustness:** Specific examples of error handling implemented (e.g., `.get()` for missing keys, `try-except` for API calls).
- **Any Ambiguity Resolutions:** Explicitly state how any ambiguities from previous prompts were resolved (e.g., "Resolved multi-hour forecast ambiguity by providing full `timeSeries` to WeatherEntity's `forecast` property.").

* TIMESTAMP: Use the current date and time (e.g., 2025-07-19 12:26 BST).
3.4 Code Quality & Focus
   * THE EXPECTATION: Code will be clean, efficient, self-evident, and kick-ass.
   * THE REQUIREMENT:
   * Every class, method, and function MUST be preceded by a comprehensive docstring explaining its purpose, arguments, and return values.
   * Use inline comments to explain the why behind complex or non-obvious logic, not the what.
   * STRICT FOCUS: Your work is confined SOLELY to the homeassistant/components/metoffice/ directory. Do not touch other files unless explicitly instructed.
   * ROBUSTNESS: Prioritize defensive programming. Assume API responses might be incomplete or malformed.
   * HOME ASSISTANT BEST PRACTICES: Adhere to the Home Assistant development guidelines for integrations (e.g., asyncio, vol, DataUpdateCoordinator).
3.5 Versioning Mandate
   * THE STANDARD: Semantic Versioning (SemVer) MAJOR.MINOR.PATCH is the only accepted versioning scheme.
   * PATCH: For backward-compatible bug fixes only.
   * MINOR: For new, backward-compatible functionality.
   * MAJOR: For any change that breaks backward compatibility.
THIS MANIFESTO IS LAW. EXECUTE ACCORDINGLY. NO FUCKING AROUND.