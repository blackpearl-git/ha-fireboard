"""The FireBoard Integration."""
import asyncio
import logging
from datetime import timedelta

import aiohttp
import async_timeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_USERNAME,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DOMAIN,
    SCAN_INTERVAL,
    API_BASE_URL,
    API_LOGIN_URL,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.NUMBER]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up FireBoard from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    coordinator = FireBoardDataUpdateCoordinator(
        hass,
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

class FireBoardDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching FireBoard data."""

    def __init__(
        self,
        hass: HomeAssistant,
        username: str,
        password: str,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.username = username
        self.password = password
        self.session = async_get_clientsession(hass)
        self.api_token = None
        self.devices = {}

    async def _async_update_data(self):
        """Fetch data from FireBoard API."""
        try:
            if not self.api_token:
                await self._async_get_token()

            async with async_timeout.timeout(10):
                devices = await self._async_get_devices()
                
                for device in devices:
                    uuid = device["UUID"]
                    if uuid not in self.devices:
                        self.devices[uuid] = device
                    
                    # Get real-time temperature data
                    temps = await self._async_get_device_temps(uuid)
                    self.devices[uuid]["latest_temps"] = temps

                    # Get Drive data if the device has Drive capability
                    if device.get("drive_enabled", False):
                        drive_data = await self._async_get_device_drive(uuid)
                        self.devices[uuid]["drive_data"] = drive_data

                return self.devices

        except asyncio.TimeoutError as err:
            raise UpdateFailed(f"Timeout communicating with API: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    async def _async_get_token(self):
        """Get API token."""
        async with self.session.post(
            API_LOGIN_URL,
            headers={"Content-Type": "application/json", "User-Agent": "Home Assistant FireBoard Integration"},
            json={"username": self.username, "password": self.password},
        ) as resp:
            if resp.status != 200:
                raise Exception(f"Failed to get token: {resp.status}")
            data = await resp.json()
            self.api_token = data["key"]

    async def _async_get_devices(self):
        """Get devices from API."""
        async with self.session.get(
            f"{API_BASE_URL}/devices.json",
            headers={
                "Authorization": f"Token {self.api_token}",
                "User-Agent": "Home Assistant FireBoard Integration"
            },
        ) as resp:
            if resp.status != 200:
                raise Exception(f"Failed to get devices: {resp.status}")
            return await resp.json()

    async def _async_get_device_temps(self, uuid):
        """Get device temperatures from API."""
        async with self.session.get(
            f"{API_BASE_URL}/devices/{uuid}/temps.json",
            headers={
                "Authorization": f"Token {self.api_token}",
                "User-Agent": "Home Assistant FireBoard Integration"
            },
        ) as resp:
            if resp.status != 200:
                raise Exception(f"Failed to get temps: {resp.status}")
            return await resp.json()

    async def _async_get_device_drive(self, uuid):
        """Get device Drive data from API."""
        async with self.session.get(
            f"{API_BASE_URL}/devices/{uuid}/drivelog.json",
            headers={
                "Authorization": f"Token {self.api_token}",
                "User-Agent": "Home Assistant FireBoard Integration"
            },
        ) as resp:
            if resp.status != 200:
                _LOGGER.debug("Drive data not available for device %s", uuid)
                return {}
            return await resp.json()

    async def async_set_drive_output(self, uuid: str, output: int) -> None:
        """Set Drive output percentage."""
        if not 0 <= output <= 100:
            raise ValueError("Drive output must be between 0 and 100")

        async with self.session.post(
            f"{API_BASE_URL}/devices/{uuid}/drive.json",
            headers={
                "Authorization": f"Token {self.api_token}",
                "Content-Type": "application/json",
                "User-Agent": "Home Assistant FireBoard Integration"
            },
            json={"output": output},
        ) as resp:
            if resp.status != 200:
                raise Exception(f"Failed to set Drive output: {resp.status}")
            return await resp.json() 