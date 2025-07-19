"""Config flow for Met Office integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import BASE_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)

SITE_LIST_URL = f"{BASE_URL}/all/json/sitelist"


class MetOfficeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the Met Office integration."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.client_id: str | None = None
        self.client_secret: str | None = None
        self.sites: list[dict[str, Any]] | None = None

    async def _async_get_sites(
        self, client_id: str, client_secret: str
    ) -> list[dict[str, Any]]:
        """Fetch available sites from the API."""
        headers = {
            "x-ibm-client-id": client_id,
            "x-ibm-client-secret": client_secret,
            "accept": "application/json",
        }
        session = async_get_clientsession(self.hass)
        try:
            resp = await session.get(
                SITE_LIST_URL, headers=headers, timeout=aiohttp.ClientTimeout(total=10)
            )
        except (TimeoutError, aiohttp.ClientError) as err:
            _LOGGER.error("Connection error: %s", err)
            raise CannotConnect from err
        if resp.status in (401, 403):
            raise InvalidAuth
        if resp.status != 200:
            raise CannotConnect
        data = await resp.json()
        sites = data.get("Locations", {}).get("Location")
        if not isinstance(sites, list):
            raise CannotConnect
        return sites

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step where credentials are entered."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self.client_id = user_input[CONF_CLIENT_ID]
            self.client_secret = user_input[CONF_CLIENT_SECRET]
            try:
                self.sites = await self._async_get_sites(
                    self.client_id, self.client_secret
                )
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            if not errors:
                return await self.async_step_location()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CLIENT_ID): str,
                    vol.Required(CONF_CLIENT_SECRET): str,
                }
            ),
            errors=errors,
        )

    async def async_step_location(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Select a forecast site from the returned list."""
        errors: dict[str, str] = {}
        assert self.sites
        options = {site["id"]: site["name"] for site in self.sites}
        if user_input is not None:
            site_id = user_input["site"]
            site_name = options[site_id]
            await self.async_set_unique_id(site_id)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=site_name,
                data={
                    CONF_CLIENT_ID: self.client_id,
                    CONF_CLIENT_SECRET: self.client_secret,
                    "site_id": site_id,
                    "site_name": site_name,
                },
            )
        return self.async_show_form(
            step_id="location",
            data_schema=vol.Schema({vol.Required("site"): vol.In(options)}),
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate invalid authentication."""
