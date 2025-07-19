"""Sensor platform for the Met Office integration."""

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
    DEGREE,
    PERCENTAGE,
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import MetOfficeDataUpdateCoordinator, get_device_info
from .const import DOMAIN


@dataclass(frozen=True)
class MetOfficeSensorDescription(SensorEntityDescription):
    """Describes Met Office sensor."""

    key: str


SENSOR_TYPES: tuple[MetOfficeSensorDescription, ...] = (
    MetOfficeSensorDescription(
        key="screenTemperature",
        name="Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    MetOfficeSensorDescription(
        key="feelsLikeTemperature",
        name="Feels Like Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    MetOfficeSensorDescription(
        key="probOfPrecipitation",
        name="Probability of Precipitation",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
    ),
    MetOfficeSensorDescription(
        key="windDirectionFrom10m",
        name="Wind Direction",
        native_unit_of_measurement=DEGREE,
    ),
    MetOfficeSensorDescription(
        key="windSpeed10m",
        name="Wind Speed",
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
    ),
    MetOfficeSensorDescription(
        key="windGust10m",
        name="Wind Gust",
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
    ),
    MetOfficeSensorDescription(
        key="screenRelativeHumidity",
        name="Humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
    ),
    MetOfficeSensorDescription(
        key="mslp",
        name="Mean Sea Level Pressure",
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.HPA,
    ),
    MetOfficeSensorDescription(
        key="uvIndex",
        name="UV Index",
    ),
    MetOfficeSensorDescription(
        key="visibility",
        name="Visibility",
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfLength.METERS,
    ),
)


class MetOfficeEntity(CoordinatorEntity[MetOfficeDataUpdateCoordinator]):
    """Base entity for Met Office sensors."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: MetOfficeDataUpdateCoordinator) -> None:
        """Initialize entity."""
        super().__init__(coordinator)
        self._attr_device_info = get_device_info(
            coordinator.latitude, coordinator.longitude, coordinator.config_entry.title
        )


class MetOfficeSensor(MetOfficeEntity, SensorEntity):
    """Representation of a Met Office sensor."""

    entity_description: MetOfficeSensorDescription

    def __init__(
        self,
        coordinator: MetOfficeDataUpdateCoordinator,
        description: MetOfficeSensorDescription,
    ) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"
        self._attr_name = f"{coordinator.config_entry.title} {description.name}"

    @property
    def native_value(self) -> StateType:
        """Return sensor value from coordinator data."""
        current = self.coordinator.data.get("forecasts", [{}])[0]
        return current.get(self.entity_description.key)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Met Office sensors."""
    coordinator: MetOfficeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [MetOfficeSensor(coordinator, description) for description in SENSOR_TYPES]
    )
