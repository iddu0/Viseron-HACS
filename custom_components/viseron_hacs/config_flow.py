"""Config flow to configure the MJPEG IP Camera integration."""

from __future__ import annotations

from collections.abc import Mapping
from http import HTTPStatus
from typing import Any

import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
from requests.exceptions import HTTPError, Timeout
import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import (
    CONF_AUTHENTICATION,
    CONF_NAME,
    CONF_VERIFY_SSL,
    HTTP_BASIC_AUTHENTICATION,
    HTTP_DIGEST_AUTHENTICATION,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError

from .const import CONF_MJPEG_URL, CONF_STILL_IMAGE_URL, DOMAIN, LOGGER


@callback
def async_get_schema(
    defaults: Mapping[str, Any], show_name: bool = False
) -> vol.Schema:
    """Return MJPEG IP Camera schema."""
    schema = {
        vol.Required(CONF_MJPEG_URL, default=defaults.get(CONF_MJPEG_URL)): str,
        vol.Optional(
            CONF_STILL_IMAGE_URL,
            description={"suggested_value": defaults.get(CONF_STILL_IMAGE_URL)},
        ): str,
        vol.Optional(
            CONF_VERIFY_SSL,
            default=defaults.get(CONF_VERIFY_SSL, True),
        ): bool,
    }

    if show_name:
        schema = {
            vol.Required(CONF_NAME, default=defaults.get(CONF_NAME)): str,
            **schema,
        }

    return vol.Schema(schema)


def validate_url(url: str, verify_ssl: bool) -> None:
    """Test if the given setting works as expected."""
    response = requests.get(url, stream=True, timeout=10, verify=verify_ssl)
    response.raise_for_status()
    response.close()

async def async_validate_input(hass: HomeAssistant, user_input: dict[str, Any]) -> dict[str, str]:
    """Validate MJPEG URLs without auth."""
    errors = {}
    for field in (CONF_MJPEG_URL, CONF_STILL_IMAGE_URL):
        url = user_input.get(field)
        if not url:
            continue
        try:
            await hass.async_add_executor_job(validate_url, url, user_input[CONF_VERIFY_SSL])
        except (OSError, HTTPError, Timeout):
            LOGGER.exception("Cannot connect to %s", url)
            errors[field] = "cannot_connect"
    return errors

class MJPEGFlowHandler(ConfigFlow, domain=DOMAIN):
    """Config flow for MJPEG IP Camera."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> MJPEGOptionsFlowHandler:
        """Get the options flow for this handler."""
        return MJPEGOptionsFlowHandler()

    async def async_step_user(
    self, user_input: dict[str, Any] | None = None
) -> ConfigFlowResult:
    """Handle a flow initialized by the user."""
    errors: dict[str, str] = {}

    if user_input is not None:
        errors = await async_validate_input(self.hass, user_input)
        if not errors:
            self._async_abort_entries_match(
                {CONF_MJPEG_URL: user_input[CONF_MJPEG_URL]}
            )

            return self.async_create_entry(
                title=user_input.get(CONF_NAME, user_input[CONF_MJPEG_URL]),
                data={},
                options={
                    CONF_MJPEG_URL: user_input[CONF_MJPEG_URL],
                    CONF_STILL_IMAGE_URL: user_input.get(CONF_STILL_IMAGE_URL),
                    CONF_VERIFY_SSL: user_input[CONF_VERIFY_SSL],
                },
            )

    else:
        user_input = {}

    return self.async_show_form(
        step_id="user",
        data_schema=async_get_schema(user_input, show_name=True),
        errors=errors,
    )

class MJPEGOptionsFlowHandler(OptionsFlow):
    """Handle MJPEG IP Camera options."""

    async def async_step_init(
    self, user_input: dict[str, Any] | None = None
) -> ConfigFlowResult:
    errors: dict[str, str] = {}

    if user_input is not None:
        errors = await async_validate_input(self.hass, user_input)
        if not errors:
            for entry in self.hass.config_entries.async_entries(DOMAIN):
                if (
                    entry.entry_id != self.config_entry.entry_id
                    and entry.options[CONF_MJPEG_URL] == user_input[CONF_MJPEG_URL]
                ):
                    errors = {CONF_MJPEG_URL: "already_configured"}

            if not errors:
                return self.async_create_entry(
                    title=user_input.get(CONF_NAME, user_input[CONF_MJPEG_URL]),
                    data={
                        CONF_MJPEG_URL: user_input[CONF_MJPEG_URL],
                        CONF_STILL_IMAGE_URL: user_input.get(CONF_STILL_IMAGE_URL),
                        CONF_VERIFY_SSL: user_input[CONF_VERIFY_SSL],
                    },
                )

    else:
        user_input = {}

    return self.async_show_form(
        step_id="init",
        data_schema=async_get_schema(user_input or self.config_entry.options),
        errors=errors,
    )

