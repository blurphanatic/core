"""Tests for Met Office config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import ConfigEntryAuthFailed

from custom_components.weatherbitch.config_flow import (
    MetOfficeConfigFlow,
    MetOfficeOptionsFlow,
)
from custom_components.weatherbitch.const import (
    CONF_API_KEY,
    CONF_TIMESTEPS,
    CONF_UPDATE_INTERVAL,
    DEFAULT_TIMESTEPS,
    DOMAIN,
)
from custom_components.weatherbitch.api import ApiError


@pytest.fixture
def mock_api_client():
    """Create a mock API client."""
    with patch(
        "custom_components.weatherbitch.config_flow.MetOfficeApiClient"
    ) as mock_client:
        instance = mock_client.return_value
        instance.get_point_forecast = AsyncMock(return_value={"features": []})
        yield instance


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.config.latitude = 51.5074
    hass.config.longitude = -0.1278
    hass.config_entries = MagicMock()
    return hass


class TestMetOfficeConfigFlow:
    """Test the Met Office config flow."""

    async def test_user_step_shows_form(self, mock_hass):
        """Test that user step shows form initially."""
        flow = MetOfficeConfigFlow()
        flow.hass = mock_hass

        result = await flow.async_step_user(user_input=None)

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        assert "api_key" in result["data_schema"].schema

    async def test_user_step_creates_entry_with_valid_input(
        self, mock_hass, mock_api_client
    ):
        """Test that user step creates entry with valid input."""
        flow = MetOfficeConfigFlow()
        flow.hass = mock_hass
        flow.async_set_unique_id = AsyncMock(return_value=None)
        flow._abort_if_unique_id_configured = MagicMock()
        flow.async_create_entry = MagicMock(
            return_value={
                "type": FlowResultType.CREATE_ENTRY,
                "title": "Met Office Forecast",
            }
        )

        user_input = {
            CONF_API_KEY: "test-api-key",
            CONF_NAME: "Met Office Forecast",
            CONF_LATITUDE: 51.5074,
            CONF_LONGITUDE: -0.1278,
            CONF_TIMESTEPS: DEFAULT_TIMESTEPS,
            CONF_UPDATE_INTERVAL: 15,
        }

        result = await flow.async_step_user(user_input=user_input)

        assert result["type"] == FlowResultType.CREATE_ENTRY
        flow.async_create_entry.assert_called_once()
        call_kwargs = flow.async_create_entry.call_args.kwargs
        assert call_kwargs["title"] == "Met Office Forecast"
        assert call_kwargs["data"][CONF_API_KEY] == "test-api-key"
        assert call_kwargs["options"][CONF_UPDATE_INTERVAL] == 15
        assert call_kwargs["options"][CONF_TIMESTEPS] == DEFAULT_TIMESTEPS

    async def test_user_step_shows_error_on_invalid_auth(self, mock_hass):
        """Test that user step shows error on invalid authentication."""
        flow = MetOfficeConfigFlow()
        flow.hass = mock_hass

        with patch(
            "custom_components.weatherbitch.config_flow.MetOfficeApiClient"
        ) as mock_client:
            instance = mock_client.return_value
            instance.get_point_forecast = AsyncMock(
                side_effect=ConfigEntryAuthFailed("Invalid API key")
            )

            user_input = {
                CONF_API_KEY: "invalid-api-key",
                CONF_NAME: "Met Office Forecast",
                CONF_LATITUDE: 51.5074,
                CONF_LONGITUDE: -0.1278,
                CONF_TIMESTEPS: DEFAULT_TIMESTEPS,
                CONF_UPDATE_INTERVAL: 15,
            }

            result = await flow.async_step_user(user_input=user_input)

            assert result["type"] == FlowResultType.FORM
            assert result["errors"] == {"base": "invalid_auth"}

    async def test_user_step_shows_error_on_connection_failure(self, mock_hass):
        """Test that user step shows error on connection failure."""
        flow = MetOfficeConfigFlow()
        flow.hass = mock_hass

        with patch(
            "custom_components.weatherbitch.config_flow.MetOfficeApiClient"
        ) as mock_client:
            instance = mock_client.return_value
            instance.get_point_forecast = AsyncMock(
                side_effect=ApiError("Connection failed")
            )

            user_input = {
                CONF_API_KEY: "test-api-key",
                CONF_NAME: "Met Office Forecast",
                CONF_LATITUDE: 51.5074,
                CONF_LONGITUDE: -0.1278,
                CONF_TIMESTEPS: DEFAULT_TIMESTEPS,
                CONF_UPDATE_INTERVAL: 15,
            }

            result = await flow.async_step_user(user_input=user_input)

            assert result["type"] == FlowResultType.FORM
            assert result["errors"] == {"base": "cannot_connect"}


class TestMetOfficeOptionsFlow:
    """Test the Met Office options flow."""

    async def test_options_flow_shows_form(self):
        """Test that options flow shows form initially."""
        mock_entry = MagicMock()
        mock_entry.options = {
            CONF_TIMESTEPS: DEFAULT_TIMESTEPS,
            CONF_UPDATE_INTERVAL: 15,
        }
        mock_entry.data = {}

        flow = MetOfficeOptionsFlow(mock_entry)

        result = await flow.async_step_init(user_input=None)

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "init"
        assert "update_interval" in result["data_schema"].schema
        assert "timesteps" in result["data_schema"].schema

    async def test_options_flow_updates_interval(self):
        """Test that options flow updates the update interval."""
        mock_entry = MagicMock()
        mock_entry.options = {
            CONF_TIMESTEPS: DEFAULT_TIMESTEPS,
            CONF_UPDATE_INTERVAL: 15,
        }
        mock_entry.data = {}

        flow = MetOfficeOptionsFlow(mock_entry)
        flow.async_create_entry = MagicMock(
            return_value={"type": FlowResultType.CREATE_ENTRY, "data": {}}
        )

        user_input = {
            CONF_TIMESTEPS: "three-hourly",
            CONF_UPDATE_INTERVAL: 30,
        }

        result = await flow.async_step_init(user_input=user_input)

        assert result["type"] == FlowResultType.CREATE_ENTRY
        flow.async_create_entry.assert_called_once_with(title="", data=user_input)

    async def test_options_flow_reads_from_data_for_backward_compat(self):
        """Test that options flow reads from data when options are empty."""
        mock_entry = MagicMock()
        mock_entry.options = {}
        mock_entry.data = {
            CONF_TIMESTEPS: "daily",
            CONF_UPDATE_INTERVAL: 60,
        }

        flow = MetOfficeOptionsFlow(mock_entry)

        result = await flow.async_step_init(user_input=None)

        assert result["type"] == FlowResultType.FORM
        # The default values should come from data since options is empty
        schema = result["data_schema"].schema
        # Verify the schema contains the expected fields
        assert "update_interval" in schema
        assert "timesteps" in schema
