"""Support for FireBoard sensors."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import FireBoardDataUpdateCoordinator
from .const import (
    ATTR_BATTERY,
    ATTR_CHANNEL,
    ATTR_DEGREETYPE,
    ATTR_HARDWARE_ID,
    DOMAIN,
)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FireBoard sensors based on a config entry."""
    coordinator: FireBoardDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for device_id, device_data in coordinator.data.items():
        # Add temperature sensors for each channel
        for temp in device_data.get("latest_temps", []):
            if temp.get("temp") is not None:  # Only add sensors with actual readings
                entities.append(
                    FireBoardTemperatureSensor(
                        coordinator,
                        device_id,
                        temp["channel"],
                        device_data.get("title", "FireBoard"),
                    )
                )

    async_add_entities(entities)

class FireBoardTemperatureSensor(CoordinatorEntity, SensorEntity):
    """Representation of a FireBoard temperature sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: FireBoardDataUpdateCoordinator,
        device_id: str,
        channel: int,
        device_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._channel = channel
        self._attr_name = f"{device_name} Channel {channel}"
        self._attr_unique_id = f"{device_id}_{channel}"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        device_data = self.coordinator.data.get(self._device_id, {})
        temps = device_data.get("latest_temps", [])
        
        for temp in temps:
            if temp["channel"] == self._channel:
                return temp.get("temp")
        return None

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        device_data = self.coordinator.data.get(self._device_id, {})
        temps = device_data.get("latest_temps", [])
        
        for temp in temps:
            if temp["channel"] == self._channel:
                # FireBoard API uses 1 for Celsius, 2 for Fahrenheit
                return UnitOfTemperature.CELSIUS if temp.get("degreetype") == 1 else UnitOfTemperature.FAHRENHEIT
        return UnitOfTemperature.FAHRENHEIT  # Default to Fahrenheit

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        device_data = self.coordinator.data.get(self._device_id, {})
        return {
            ATTR_HARDWARE_ID: device_data.get("hardware_id"),
            ATTR_CHANNEL: self._channel,
            ATTR_DEGREETYPE: "Celsius" if self.native_unit_of_measurement == UnitOfTemperature.CELSIUS else "Fahrenheit",
            ATTR_BATTERY: device_data.get("battery"),
        } 