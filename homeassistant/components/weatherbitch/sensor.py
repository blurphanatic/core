"""Sensor entities for the Met Office integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
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
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import MetOfficeDataUpdateCoordinator
from .const import DOMAIN


@dataclass(frozen=True)
class MetOfficeSensorDescription(SensorEntityDescription):
    """Describe a Met Office sensor."""

    key: str


SENSOR_TYPES: tuple[MetOfficeSensorDescription, ...] = (
    MetOfficeSensorDescription(
        key="screenTemperature",
        name="Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    MetOfficeSensorDescription(
        key="feelsLikeTemperature",
        name="Feels Like Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    MetOfficeSensorDescription(
        key="probOfPrecipitation",
        name="Probability of Precipitation",
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
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
    ),
    MetOfficeSensorDescription(
        key="windGust10m",
        name="Wind Gust",
        device_class=SensorDeviceClass.WIND_SPEED,
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
    ),
    MetOfficeSensorDescription(
        key="screenRelativeHumidity",
        name="Humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
    ),
    MetOfficeSensorDescription(
        key="mslp",
        name="Mean Sea Level Pressure",
        device_class=SensorDeviceClass.PRESSURE,
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
        native_unit_of_measurement=UnitOfLength.METERS,
    ),
)


class MetOfficeSensor(CoordinatorEntity[MetOfficeDataUpdateCoordinator], SensorEntity):
    """Representation of a Met Office sensor."""

    entity_description: MetOfficeSensorDescription

    def __init__(
        self,
        coordinator: MetOfficeDataUpdateCoordinator,
        description: MetOfficeSensorDescription,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_name = f"{config_entry.title} {description.name}"
        self._attr_unique_id = f"{config_entry.entry_id}_{description.key}"

    @property
    def native_value(self) -> Any:
        """Return the sensor value from the latest data."""
        forecast = self.coordinator.data.get("forecasts", [{}])[0]
        return forecast.get(self.entity_description.key)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Met Office sensors based on a config entry."""
    coordinator: MetOfficeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            MetOfficeSensor(coordinator, description, entry)
            for description in SENSOR_TYPES
        ]
    )
