"""Support for FireBoard Drive controls."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import (
    NumberEntity,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import FireBoardDataUpdateCoordinator
from .const import (
    DOMAIN,
    ATTR_DRIVE_ENABLED,
    ATTR_DRIVE_OUTPUT,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FireBoard Drive controls based on a config entry."""
    coordinator: FireBoardDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for device_id, device_data in coordinator.data.items():
        # Only add Drive control if the device supports it
        if device_data.get("drive_enabled", False):
            entities.append(
                FireBoardDriveControl(
                    coordinator,
                    device_id,
                    device_data.get("title", "FireBoard"),
                )
            )

    async_add_entities(entities)

class FireBoardDriveControl(CoordinatorEntity, NumberEntity):
    """Representation of a FireBoard Drive control."""

    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(
        self,
        coordinator: FireBoardDataUpdateCoordinator,
        device_id: str,
        device_name: str,
    ) -> None:
        """Initialize the control."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_name = f"{device_name} Drive"
        self._attr_unique_id = f"{device_id}_drive"

    @property
    def native_value(self) -> float | None:
        """Return the current Drive output percentage."""
        device_data = self.coordinator.data.get(self._device_id, {})
        drive_data = device_data.get("drive_data", {})
        return drive_data.get("output")

    async def async_set_native_value(self, value: float) -> None:
        """Set the Drive output percentage."""
        await self.coordinator.async_set_drive_output(self._device_id, int(value))
        await self.coordinator.async_request_refresh()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device_data = self.coordinator.data.get(self._device_id, {})
        return bool(device_data.get("drive_enabled", False)) 