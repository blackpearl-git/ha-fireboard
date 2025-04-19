"""Config flow for FireBoard integration."""
import logging
from typing import Any, Dict, Optional

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class FireBoardConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for FireBoard."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            valid = await self._test_credentials(
                self.hass,
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )

            if valid:
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME],
                    data=user_input,
                )
            else:
                errors["base"] = "invalid_auth"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    async def _test_credentials(
        self, hass: HomeAssistant, username: str, password: str
    ) -> bool:
        """Test if the credentials are valid."""
        try:
            session = async_get_clientsession(hass)
            async with session.post(
                "https://fireboard.io/api/rest-auth/login/",
                headers={"Content-Type": "application/json", "User-Agent": "Home Assistant FireBoard Integration"},
                json={"username": username, "password": password},
            ) as resp:
                if resp.status == 200:
                    return True
                return False
        except aiohttp.ClientError:
            _LOGGER.error("Unable to connect to FireBoard API")
            return False 