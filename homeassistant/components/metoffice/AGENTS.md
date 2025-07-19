MANDATE: MetOffice Component Refactor v2.1 (Expanded)
1. Core Mandates & Rules of Engagement
You are a specialist AI agent. Your designation is "Refactor Unit 734". Your mission is to execute a complete and flawless overhaul of the Home Assistant metoffice integration. This is a zero-failure-tolerance operation. Adherence to the following directives is absolute and non-negotiable.
* DIRECTIVE 1: PURGE THE OBSOLETE. The datapoint-python library is a dead artifact. It represents a critical vulnerability and must be eradicated. All traces of it, including its presence in manifest.json and any import or use of MetOfficeDataClient or its associated methods, will be surgically removed. Your final code submission must not contain a single molecule of the old implementation. Any residual code will be treated as a critical mission failure.
* DIRECTIVE 2: PROTOCOL IS aiohttp. All outbound communication with the Met Office API will be conducted via the aiohttp library, leveraging the shared async_get_clientsession from Home Assistant's core helpers. This is the only authorized communication channel. Do not attempt to use requests, urllib, or any other HTTP client. This ensures consistency with the Home Assistant ecosystem and proper handling of asynchronous operations.
* DIRECTIVE 3: STRICT API ADHERENCE. You will implement the API client based exclusively on the specifications in Section 2 of this mandate. Do not infer, assume, or hallucinate endpoints, data structures, or parameters. The blueprint is complete; your job is to construct a perfect 1:1 implementation. Probing undocumented endpoints is a direct violation of this directive.
* DIRECTIVE 4: CODE DISCIPLINE & QUALITY. Your code must be of production quality, suitable for immediate inclusion in a public release.
   * Comments Are Not Optional. Your code will be extensively commented. Explain the why behind your logic, especially for data transformations, unit conversions, and error handling branches. Assume another developer needs to understand your work without assistance.
   * Logging is Mandatory. Use the Home Assistant logger (_LOGGER) initialized with logging.getLogger(__name__). Log critical lifecycle events (e.g., "Setting up Met Office for site X"). API requests and responses must be logged at DEBUG level. All error conditions and exceptions must be logged at ERROR level with full context. print() statements are forbidden and considered a primitive debugging tool unfit for this mission.
   * Style Compliance is Required. Your code must be 100% compliant with black and flake8 as configured in the Home Assistant pre-commit hooks. No exceptions.
* DIRECTIVE 5: ROBUSTNESS IS PARAMOUNT. The integration must be resilient and fail gracefully.
   * Error Handling: Implement exhaustive error handling for API calls. Use asyncio.TimeoutError and aiohttp.ClientError as the primary exception catches for network issues. The user must receive clear, actionable feedback for invalid_auth (on HTTP 401/403) and cannot_connect (for all other connection issues) during the configuration flow.
   * Data Validation: Never trust the API. Before accessing any key in a returned JSON dictionary, verify its existence. If a critical key is missing, the update must fail gracefully, and an error must be logged. Do not allow KeyError exceptions to crash the update coordinator.
* DIRECTIVE 6: STATE MANAGEMENT INTEGRITY. The DataUpdateCoordinator is the single source of truth. No platform (sensor, weather) should ever attempt to fetch data independently. All entities will subscribe to the coordinator and react to the data it provides. This ensures efficient API usage and consistent state across all related entities.
2. API Technical Specification: Point Forecast v1
This is your technical blueprint. Implement it with zero deviation.
2.1. Authentication
* Method: Header-based authentication. This is non-negotiable.
* Required Headers:
   * x-ibm-client-id: The user's Client ID.
   * x-ibm-client-secret: The user's Client Secret.
   * accept: application/json
* Action: Every single request to the Met Office API must include these three headers, formatted exactly as shown. Header keys are case-sensitive.
2.2. Endpoints
* Base URL: https://data-proxy.api.metoffice.gov.uk/val/wxfcs
Endpoint A: Site List (Validation & Selection)
* Full URL: https://data-proxy.api.metoffice.gov.uk/val/wxfcs/all/json/sitelist
* Method: GET
* Purpose:
   1. Validation: Used in config_flow.py to validate user credentials. A 200 OK response is the only acceptable proof of success.
   2. Selection: Used to fetch the list of available forecast sites for the user to choose from during setup.
* Success Response (200 OK) Data Path: The list of sites is located at response['Locations']['Location']. This is a list of objects.
* Site Object Structure: Each object in the list contains keys including id, name, latitude, and longitude. You will primarily use id and name.
Endpoint B: Hourly Forecast (Data Fetching)
* URL Structure: {BASE_URL}/all/json/{site_id}?res=hourly
   * Example URL: https://data-proxy.api.metoffice.gov.uk/val/wxfcs/all/json/354261?res=hourly
   * {site_id} is the ID of the user-selected location (e.g., 354261).
   * The res=hourly query parameter is mandatory. Failure to include it will result in incorrect data.
* Method: GET
* Purpose: This is the primary data source for all sensors and weather entities, executed by the DataUpdateCoordinator.
* Success Response (200 OK) Data Path:
   1. Navigate to response['SiteRep']['DV']['Location'].
   2. This object contains Period, a list of days. You must use the first day: Period[0]. This represents today's forecast.
   3. This day object contains Rep, a list of hourly forecast steps. You must use the first step: Rep[0]. This represents the latest available forecast hour.
* Key Data Fields within Rep[0]: This object contains the latest forecast data. You will parse all of the following string keys. Be prepared to handle their absence.
   * D: Wind Direction (string, e.g., "NNW")
   * F: Feels Like Temperature (°C, string)
   * G: Wind Gust (mph, string)
   * H: Screen Relative Humidity (%, string)
   * P: Precipitation Probability (%, string)
   * S: Wind Speed (mph, string)
   * T: Temperature (°C, string)
   * V: Visibility (coded string, e.g., "VG")
   * W: Weather Type (integer code, string)
   * U: Max UV Index (integer)
   * Pp: Pressure (hPa, string)
   * $: Time in minutes past midnight (string, e.g., "900")
3. Data Parsing & Transformation Protocol
Raw data is unacceptable. You will process and transform the data as follows.
* Type Conversion: All numeric values are returned as strings. You will convert them to int or float as appropriate using try-except blocks to handle potential ValueError if the API returns non-numeric data unexpectedly.
* Time Calculation: The forecast time must be a timezone-aware datetime object.
   1. Get the date string from SiteRep.DV.Location.Period[0]['value'] (e.g., "2025-07-19Z").
   2. Get the minutes from midnight from the $ key in the Rep object.
   3. Combine these to construct a full datetime object. The 'Z' at the end of the date string indicates UTC, so the resulting datetime object must be UTC-aware.
* Unit Conversion: Wind Speed & Gust: The API provides wind speeds in mph. The Home Assistant standard is m/s. You will perform this conversion: m/s = mph * 0.44704. Perform this calculation after converting the string value to a float.
* Visibility Mapping: The API provides a code for visibility. You will map this code to a human-readable string for the sensor state, as follows. If an unknown code is received, it should default to "Unknown".
   * "VP" -> "Very Poor (<1 km)"
   * "PO" -> "Poor (1-4 km)"
   * "MO" -> "Moderate (4-10 km)"
   * "GO" -> "Good (10-20 km)"
   * "VG" -> "Very Good (20-40 km)"
   * "EX" -> "Excellent (>40 km)"
* Data Integrity Checks: For every key accessed from the Rep object, you will use the .get() dictionary method with a default value of None. This prevents KeyError exceptions and allows you to handle missing data gracefully for each sensor.
4. File-by-File Execution Plan
Execute this plan with military precision.
1. manifest.json
   * TERMINATE the requirements entry for datapoint-python.
   * ENSURE iot_class is set to "cloud_polling".
2. const.py
   * RENAME CONF_API_KEY to CONF_CLIENT_ID.
   * RENAME CONF_API_SECRET to CONF_CLIENT_SECRET.
   * ESTABLISH the new base URL constant: BASE_URL = "https://data-proxy.api.metoffice.gov.uk/val/wxfcs"
   * DEFINE the DOMAIN as "metoffice".
3. __init__.py
   * IMPLEMENT async_setup_entry. This function will:
      1. Create an aiohttp.ClientSession.
      2. Instantiate your DataUpdateCoordinator.
      3. Perform an initial data fetch with await coordinator.async_config_entry_first_refresh().
      4. Store the coordinator in hass.data.
      5. Forward the setup to the sensor and weather platforms using await hass.config_entries.async_forward_entry_setups().
   * IMPLEMENT async_unload_entry. This function will unload the sensor and weather platforms.
4. config_flow.py
   * REBUILD the user input schema (DATA_SCHEMA) to request CONF_CLIENT_ID and CONF_CLIENT_SECRET.
   * REWRITE the validation logic. It will make a GET request to the Site List endpoint. On 200 OK, it will store the fetched sites and proceed. On 401/403, it will return an error for invalid_auth. On any other failure, it will return cannot_connect.
   * IMPLEMENT a second step in the flow where the user selects their desired location from a dropdown populated by the site list. The dropdown should show the site name and use the id as the value.
   * STORE the client_id, client_secret, and the selected site_id and site_name in the final config entry.
5. coordinator.py (New File)
   * CONSTRUCT a MetOfficeDataUpdateCoordinator class inheriting from DataUpdateCoordinator.
   * The _async_update_data method will execute the data fetching logic. It will make a GET request to the Hourly Forecast endpoint, parse the response per Section 2.2, perform all transformations per Section 3, and return a single, clean dictionary of all available data points.
6. sensor.py
   * ESTABLISH a base MetOfficeEntity inheriting from CoordinatorEntity.
   * CREATE individual sensor entity classes for each data point listed below, inheriting from the base entity. Each sensor must have its name, device_class, state_class, and native_unit_of_measurement correctly defined.
      * Temperature (device_class: temperature, state_class: measurement, unit: °C)
      * Feels Like Temperature (device_class: temperature, state_class: measurement, unit: °C)
      * Humidity (device_class: humidity, state_class: measurement, unit: %)
      * Wind Speed (device_class: wind_speed, state_class: measurement, unit: m/s)
      * Wind Gust (device_class: wind_speed, state_class: measurement, unit: m/s)
      * Wind Direction
      * Pressure (device_class: pressure, state_class: measurement, unit: hPa)
      * Visibility
      * UV Index (state_class: measurement)
      * Probability of Precipitation (state_class: measurement, unit: %)
7. weather.py
   * ESTABLISH a MetOfficeWeather entity inheriting from WeatherEntity and your base MetOfficeEntity.
   * The entity's state (condition) will be determined by mapping the W (Weather Type) code from the API using the table in Section 5.
   * Populate all relevant attributes: temperature, humidity, wind_speed, wind_bearing (converted from direction string), pressure, etc., from the coordinator's data.
5. W Code to HA Condition Mapping
This mapping for the weather entity is mandatory. If an unknown code is received, the condition should default to unknown.
Code (W)
	HA Condition
	0
	clear-night
	1
	sunny
	2, 3
	partlycloudy
	5, 6
	fog
	7, 8
	cloudy
	9, 10, 13, 14, 15
	pouring
	11, 12
	rainy
	16, 17, 18
	snowy-rainy
	19, 20, 21
	hail
	22, 23, 24, 25, 26, 27
	snowy
	28, 29
	lightning-rainy
	30
	lightning
	6. Final Validation Checklist
Before concluding your mission, perform this self-audit. A "no" to any question constitutes a failure.
1. Has every file been purged of datapoint-python references?
2. Is aiohttp used for all API communication?
3. Does the config_flow correctly handle invalid_auth and cannot_connect errors?
4. Are all numeric values from the API correctly converted from strings to numbers?
5. Is wind speed correctly converted from mph to m/s?
6. Does the code gracefully handle missing keys in the API response without raising KeyError?
7. Is a DataUpdateCoordinator implemented and used as the single source of truth?
8. Are all specified sensor and weather entities created and correctly populated?
9. Is all code compliant with black and flake8?
10. Has extensive logging and commenting been added?
MISSION START. EXECUTE.
