"""Met Office sensor platform."""

# pylint: disable=hass-enforce-class-module

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import get_device_info
from .const import DOMAIN
from .coordinator import MetOfficeDataUpdateCoordinator


@dataclass(frozen=True)
class MetOfficeSensorEntityDescription(SensorEntityDescription):
    """Describe Met Office sensor."""

    value_key: str


SENSOR_DESCRIPTIONS: tuple[MetOfficeSensorEntityDescription, ...] = (
    MetOfficeSensorEntityDescription(
        key="temperature",
        value_key="temperature",
        name="Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    MetOfficeSensorEntityDescription(
        key="feels_like_temperature",
        value_key="feels_like_temperature",
        name="Feels Like Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    MetOfficeSensorEntityDescription(
        key="humidity",
        value_key="humidity",
        name="Humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
    ),
    MetOfficeSensorEntityDescription(
        key="wind_speed",
        value_key="wind_speed",
        name="Wind Speed",
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
    ),
    MetOfficeSensorEntityDescription(
        key="wind_gust",
        value_key="wind_gust",
        name="Wind Gust",
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
    ),
    MetOfficeSensorEntityDescription(
        key="wind_direction",
        value_key="wind_direction",
        name="Wind Direction",
        device_class=SensorDeviceClass.WIND_DIRECTION,
        state_class=SensorStateClass.MEASUREMENT_ANGLE,
    ),
    MetOfficeSensorEntityDescription(
        key="pressure",
        value_key="pressure",
        name="Pressure",
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.HPA,
    ),
    MetOfficeSensorEntityDescription(
        key="visibility",
        value_key="visibility",
        name="Visibility",
    ),
    MetOfficeSensorEntityDescription(
        key="uv_index",
        value_key="uv_index",
        name="UV Index",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MetOfficeSensorEntityDescription(
        key="precipitation_probability",
        value_key="precipitation_probability",
        name="Probability of Precipitation",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
    ),
)


class MetOfficeEntity(CoordinatorEntity[MetOfficeDataUpdateCoordinator]):
    """Base Met Office entity."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: MetOfficeDataUpdateCoordinator) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._attr_device_info = get_device_info(
            coordinator.site_id, coordinator.site_name
        )


class MetOfficeSensor(MetOfficeEntity, SensorEntity):
    """Representation of a Met Office sensor."""

    entity_description: MetOfficeSensorEntityDescription

    def __init__(
        self,
        coordinator: MetOfficeDataUpdateCoordinator,
        description: MetOfficeSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.site_id}_{description.key}"

    @property
    def native_value(self) -> StateType:
        """Return the sensor value."""
        return self.coordinator.data.get(self.entity_description.value_key)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up sensors."""
    coordinator: MetOfficeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            MetOfficeSensor(coordinator, description)
            for description in SENSOR_DESCRIPTIONS
        ]
    )
