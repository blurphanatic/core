"""Tests for sensor entities."""

from __future__ import annotations

from unittest.mock import MagicMock
import pytest

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    DEGREE,
    PERCENTAGE,
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)

from custom_components.weatherbitch.sensor import (
    MetOfficeSensor,
    MetOfficeSensorDescription,
    SENSOR_TYPES,
)


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator with sample data."""
    coordinator = MagicMock()
    coordinator.config_entry = MagicMock()
    coordinator.config_entry.entry_id = "test_entry_id"
    coordinator.config_entry.title = "Test Location"
    coordinator.latitude = 51.5074
    coordinator.longitude = -0.1278
    coordinator.data = {
        "forecasts": [
            {
                "time": "2024-01-20T12:00:00Z",
                "screenTemperature": 15.5,
                "feelsLikeTemperature": 13.2,
                "mslp": 1013.25,
                "screenRelativeHumidity": 75,
                "windSpeed10m": 5.5,
                "windGust10m": 8.2,
                "windDirectionFrom10m": 180,
                "visibility": 10000,
                "dewPoint": 10.5,
                "uvIndex": 3,
                "totalCloudAmount": 50,
                "significantWeatherCode": 1,
                "probOfPrecipitation": 20,
                "totalPrecipAmount": 0.5,
            }
        ]
    }
    return coordinator


class TestSensorTypesDefinition:
    """Test all sensor types are defined correctly."""

    def test_sensor_types_count(self):
        """Test the correct number of sensor types are defined."""
        # Original 10 + 3 new sensors = 13
        assert len(SENSOR_TYPES) == 13

    def test_temperature_sensor_definition(self):
        """Test temperature sensor is defined correctly."""
        temp_sensor = next(s for s in SENSOR_TYPES if s.key == "screenTemperature")
        assert temp_sensor.name == "Temperature"
        assert temp_sensor.device_class == SensorDeviceClass.TEMPERATURE
        assert temp_sensor.state_class == SensorStateClass.MEASUREMENT
        assert temp_sensor.native_unit_of_measurement == UnitOfTemperature.CELSIUS

    def test_feels_like_sensor_definition(self):
        """Test feels like temperature sensor is defined correctly."""
        sensor = next(s for s in SENSOR_TYPES if s.key == "feelsLikeTemperature")
        assert sensor.name == "Feels Like Temperature"
        assert sensor.device_class == SensorDeviceClass.TEMPERATURE
        assert sensor.native_unit_of_measurement == UnitOfTemperature.CELSIUS

    def test_precipitation_probability_sensor_definition(self):
        """Test precipitation probability sensor is defined correctly."""
        sensor = next(s for s in SENSOR_TYPES if s.key == "probOfPrecipitation")
        assert sensor.name == "Probability of Precipitation"
        assert sensor.state_class == SensorStateClass.MEASUREMENT
        assert sensor.native_unit_of_measurement == PERCENTAGE

    def test_wind_direction_sensor_definition(self):
        """Test wind direction sensor is defined correctly."""
        sensor = next(s for s in SENSOR_TYPES if s.key == "windDirectionFrom10m")
        assert sensor.name == "Wind Direction"
        assert sensor.native_unit_of_measurement == DEGREE

    def test_wind_speed_sensor_definition(self):
        """Test wind speed sensor is defined correctly."""
        sensor = next(s for s in SENSOR_TYPES if s.key == "windSpeed10m")
        assert sensor.name == "Wind Speed"
        assert sensor.device_class == SensorDeviceClass.WIND_SPEED
        assert sensor.native_unit_of_measurement == UnitOfSpeed.METERS_PER_SECOND

    def test_wind_gust_sensor_definition(self):
        """Test wind gust sensor is defined correctly."""
        sensor = next(s for s in SENSOR_TYPES if s.key == "windGust10m")
        assert sensor.name == "Wind Gust"
        assert sensor.device_class == SensorDeviceClass.WIND_SPEED
        assert sensor.native_unit_of_measurement == UnitOfSpeed.METERS_PER_SECOND

    def test_humidity_sensor_definition(self):
        """Test humidity sensor is defined correctly."""
        sensor = next(s for s in SENSOR_TYPES if s.key == "screenRelativeHumidity")
        assert sensor.name == "Humidity"
        assert sensor.device_class == SensorDeviceClass.HUMIDITY
        assert sensor.native_unit_of_measurement == PERCENTAGE

    def test_pressure_sensor_definition(self):
        """Test pressure sensor is defined correctly."""
        sensor = next(s for s in SENSOR_TYPES if s.key == "mslp")
        assert sensor.name == "Mean Sea Level Pressure"
        assert sensor.device_class == SensorDeviceClass.PRESSURE
        assert sensor.native_unit_of_measurement == UnitOfPressure.HPA

    def test_uv_index_sensor_definition(self):
        """Test UV index sensor is defined correctly."""
        sensor = next(s for s in SENSOR_TYPES if s.key == "uvIndex")
        assert sensor.name == "UV Index"
        assert sensor.state_class == SensorStateClass.MEASUREMENT

    def test_visibility_sensor_definition(self):
        """Test visibility sensor is defined correctly."""
        sensor = next(s for s in SENSOR_TYPES if s.key == "visibility")
        assert sensor.name == "Visibility"
        assert sensor.device_class == SensorDeviceClass.DISTANCE
        assert sensor.native_unit_of_measurement == UnitOfLength.METERS


class TestNewSensorDefinitions:
    """Test newly added sensor definitions."""

    def test_dew_point_sensor_definition(self):
        """Test dew point sensor is defined correctly."""
        sensor = next(s for s in SENSOR_TYPES if s.key == "dewPoint")
        assert sensor.name == "Dew Point"
        assert sensor.device_class == SensorDeviceClass.TEMPERATURE
        assert sensor.state_class == SensorStateClass.MEASUREMENT
        assert sensor.native_unit_of_measurement == UnitOfTemperature.CELSIUS

    def test_precipitation_amount_sensor_definition(self):
        """Test precipitation amount sensor is defined correctly."""
        sensor = next(s for s in SENSOR_TYPES if s.key == "totalPrecipAmount")
        assert sensor.name == "Precipitation"
        assert sensor.device_class == SensorDeviceClass.PRECIPITATION
        assert sensor.state_class == SensorStateClass.MEASUREMENT
        assert sensor.native_unit_of_measurement == UnitOfLength.MILLIMETERS

    def test_cloud_coverage_sensor_definition(self):
        """Test cloud coverage sensor is defined correctly."""
        sensor = next(s for s in SENSOR_TYPES if s.key == "totalCloudAmount")
        assert sensor.name == "Cloud Coverage"
        assert sensor.state_class == SensorStateClass.MEASUREMENT
        assert sensor.native_unit_of_measurement == PERCENTAGE


class TestSensorValues:
    """Test sensor reads from current conditions correctly."""

    def test_temperature_sensor_value(self, mock_coordinator):
        """Test temperature sensor reads correct value."""
        description = next(s for s in SENSOR_TYPES if s.key == "screenTemperature")
        sensor = MetOfficeSensor(mock_coordinator, description)
        assert sensor.native_value == 15.5

    def test_feels_like_sensor_value(self, mock_coordinator):
        """Test feels like sensor reads correct value."""
        description = next(s for s in SENSOR_TYPES if s.key == "feelsLikeTemperature")
        sensor = MetOfficeSensor(mock_coordinator, description)
        assert sensor.native_value == 13.2

    def test_humidity_sensor_value(self, mock_coordinator):
        """Test humidity sensor reads correct value."""
        description = next(s for s in SENSOR_TYPES if s.key == "screenRelativeHumidity")
        sensor = MetOfficeSensor(mock_coordinator, description)
        assert sensor.native_value == 75

    def test_pressure_sensor_value(self, mock_coordinator):
        """Test pressure sensor reads correct value."""
        description = next(s for s in SENSOR_TYPES if s.key == "mslp")
        sensor = MetOfficeSensor(mock_coordinator, description)
        assert sensor.native_value == 1013.25

    def test_wind_speed_sensor_value(self, mock_coordinator):
        """Test wind speed sensor reads correct value."""
        description = next(s for s in SENSOR_TYPES if s.key == "windSpeed10m")
        sensor = MetOfficeSensor(mock_coordinator, description)
        assert sensor.native_value == 5.5

    def test_wind_gust_sensor_value(self, mock_coordinator):
        """Test wind gust sensor reads correct value."""
        description = next(s for s in SENSOR_TYPES if s.key == "windGust10m")
        sensor = MetOfficeSensor(mock_coordinator, description)
        assert sensor.native_value == 8.2

    def test_wind_direction_sensor_value(self, mock_coordinator):
        """Test wind direction sensor reads correct value."""
        description = next(s for s in SENSOR_TYPES if s.key == "windDirectionFrom10m")
        sensor = MetOfficeSensor(mock_coordinator, description)
        assert sensor.native_value == 180

    def test_visibility_sensor_value(self, mock_coordinator):
        """Test visibility sensor reads correct value."""
        description = next(s for s in SENSOR_TYPES if s.key == "visibility")
        sensor = MetOfficeSensor(mock_coordinator, description)
        assert sensor.native_value == 10000

    def test_uv_index_sensor_value(self, mock_coordinator):
        """Test UV index sensor reads correct value."""
        description = next(s for s in SENSOR_TYPES if s.key == "uvIndex")
        sensor = MetOfficeSensor(mock_coordinator, description)
        assert sensor.native_value == 3

    def test_precipitation_probability_sensor_value(self, mock_coordinator):
        """Test precipitation probability sensor reads correct value."""
        description = next(s for s in SENSOR_TYPES if s.key == "probOfPrecipitation")
        sensor = MetOfficeSensor(mock_coordinator, description)
        assert sensor.native_value == 20


class TestNewSensorValues:
    """Test newly added sensor values."""

    def test_dew_point_sensor_value(self, mock_coordinator):
        """Test dew point sensor reads correct value."""
        description = next(s for s in SENSOR_TYPES if s.key == "dewPoint")
        sensor = MetOfficeSensor(mock_coordinator, description)
        assert sensor.native_value == 10.5

    def test_precipitation_amount_sensor_value(self, mock_coordinator):
        """Test precipitation amount sensor reads correct value."""
        description = next(s for s in SENSOR_TYPES if s.key == "totalPrecipAmount")
        sensor = MetOfficeSensor(mock_coordinator, description)
        assert sensor.native_value == 0.5

    def test_cloud_coverage_sensor_value(self, mock_coordinator):
        """Test cloud coverage sensor reads correct value."""
        description = next(s for s in SENSOR_TYPES if s.key == "totalCloudAmount")
        sensor = MetOfficeSensor(mock_coordinator, description)
        assert sensor.native_value == 50


class TestSensorMissingData:
    """Test sensor handles missing data gracefully."""

    def test_missing_key_returns_none(self, mock_coordinator):
        """Test sensor returns None for missing key."""
        # Create a custom description for a non-existent key
        description = MetOfficeSensorDescription(
            key="nonExistentKey",
            name="Non Existent",
        )
        sensor = MetOfficeSensor(mock_coordinator, description)
        assert sensor.native_value is None

    def test_empty_forecasts_returns_none(self, mock_coordinator):
        """Test sensor returns None when forecasts is empty."""
        mock_coordinator.data = {"forecasts": [{}]}
        description = next(s for s in SENSOR_TYPES if s.key == "screenTemperature")
        sensor = MetOfficeSensor(mock_coordinator, description)
        assert sensor.native_value is None

    def test_none_data_returns_none(self, mock_coordinator):
        """Test sensor returns None when data is None."""
        mock_coordinator.data = None
        description = next(s for s in SENSOR_TYPES if s.key == "screenTemperature")
        sensor = MetOfficeSensor(mock_coordinator, description)
        assert sensor.native_value is None

    def test_empty_data_dict_returns_none(self, mock_coordinator):
        """Test sensor returns None when data is empty dict."""
        mock_coordinator.data = {}
        description = next(s for s in SENSOR_TYPES if s.key == "screenTemperature")
        sensor = MetOfficeSensor(mock_coordinator, description)
        assert sensor.native_value is None


class TestDataStructureFallback:
    """Test fallback between current and forecasts data structures."""

    def test_current_key_takes_precedence(self, mock_coordinator):
        """Test current key takes precedence over forecasts key."""
        mock_coordinator.data["current"] = {
            "screenTemperature": 20.0,
        }
        description = next(s for s in SENSOR_TYPES if s.key == "screenTemperature")
        sensor = MetOfficeSensor(mock_coordinator, description)
        assert sensor.native_value == 20.0

    def test_fallback_to_forecasts_when_current_absent(self, mock_coordinator):
        """Test sensor reads from forecasts when current is absent."""
        # Data only has forecasts key
        description = next(s for s in SENSOR_TYPES if s.key == "screenTemperature")
        sensor = MetOfficeSensor(mock_coordinator, description)
        assert sensor.native_value == 15.5


class TestSensorEntityAttributes:
    """Test sensor entity attributes."""

    def test_unique_id_format(self, mock_coordinator):
        """Test unique ID is properly formatted."""
        description = next(s for s in SENSOR_TYPES if s.key == "screenTemperature")
        sensor = MetOfficeSensor(mock_coordinator, description)
        assert sensor._attr_unique_id == "test_entry_id_screenTemperature"

    def test_name_format(self, mock_coordinator):
        """Test name includes location title."""
        description = next(s for s in SENSOR_TYPES if s.key == "screenTemperature")
        sensor = MetOfficeSensor(mock_coordinator, description)
        assert sensor._attr_name == "Test Location Temperature"

    def test_has_entity_name_is_true(self, mock_coordinator):
        """Test has_entity_name is enabled."""
        description = next(s for s in SENSOR_TYPES if s.key == "screenTemperature")
        sensor = MetOfficeSensor(mock_coordinator, description)
        assert sensor._attr_has_entity_name is True
