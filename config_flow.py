"""Config flow for Met Office integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.core import callback
from homeassistant.exceptions import ConfigEntryAuthFailed

from .api import ApiError, MetOfficeApiClient
from .const import (
    CONF_API_KEY,
    CONF_TIMESTEPS,
    CONF_UPDATE_INTERVAL,
    DEFAULT_TIMESTEPS,
    DOMAIN,
    MAX_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
    TIMESTEP_OPTIONS,
    UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class MetOfficeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the Met Office integration."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> MetOfficeOptionsFlow:
        """Get the options flow handler."""
        return MetOfficeOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step of the config flow."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY]
            latitude = user_input.get(CONF_LATITUDE, self.hass.config.latitude)
            longitude = user_input.get(CONF_LONGITUDE, self.hass.config.longitude)
            name = user_input[CONF_NAME]
            timesteps = user_input[CONF_TIMESTEPS]
            update_interval = user_input[CONF_UPDATE_INTERVAL]

            client = MetOfficeApiClient(self.hass, api_key)
            try:
                await client.get_point_forecast(latitude, longitude)
            except ConfigEntryAuthFailed:
                errors["base"] = "invalid_auth"
            except ApiError:
                errors["base"] = "cannot_connect"
            else:
                # Check for existing entry with same location
                await self.async_set_unique_id(f"{latitude}_{longitude}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=name,
                    data={
                        CONF_API_KEY: api_key,
                        CONF_LATITUDE: latitude,
                        CONF_LONGITUDE: longitude,
                    },
                    options={
                        CONF_TIMESTEPS: timesteps,
                        CONF_UPDATE_INTERVAL: update_interval,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                    vol.Required(CONF_NAME, default="Met Office Forecast"): str,
                    vol.Required(
                        CONF_LATITUDE, default=self.hass.config.latitude
                    ): vol.Coerce(float),
                    vol.Required(
                        CONF_LONGITUDE, default=self.hass.config.longitude
                    ): vol.Coerce(float),
                    vol.Required(CONF_TIMESTEPS, default=DEFAULT_TIMESTEPS): vol.In(
                        TIMESTEP_OPTIONS
                    ),
                    vol.Required(
                        CONF_UPDATE_INTERVAL,
                        default=int(UPDATE_INTERVAL.total_seconds() // 60),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(
                            min=int(MIN_UPDATE_INTERVAL.total_seconds() // 60),
                            max=int(MAX_UPDATE_INTERVAL.total_seconds() // 60),
                        ),
                    ),
                }
            ),
            errors=errors,
        )


class MetOfficeOptionsFlow(OptionsFlow):
    """Handle options flow for Met Office integration."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Get current values from options, fall back to data for backward compatibility
        current_timesteps = self.config_entry.options.get(
            CONF_TIMESTEPS,
            self.config_entry.data.get(CONF_TIMESTEPS, DEFAULT_TIMESTEPS),
        )
        current_interval = self.config_entry.options.get(
            CONF_UPDATE_INTERVAL,
            self.config_entry.data.get(
                CONF_UPDATE_INTERVAL, int(UPDATE_INTERVAL.total_seconds() // 60)
            ),
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_TIMESTEPS,
                        default=current_timesteps,
                    ): vol.In(TIMESTEP_OPTIONS),
                    vol.Required(
                        CONF_UPDATE_INTERVAL,
                        default=current_interval,
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(
                            min=int(MIN_UPDATE_INTERVAL.total_seconds() // 60),
                            max=int(MAX_UPDATE_INTERVAL.total_seconds() // 60),
                        ),
                    ),
                }
            ),
        )
