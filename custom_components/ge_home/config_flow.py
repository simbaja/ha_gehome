"""Config flow for GE Home integration."""

import logging
from typing import Dict, List, Optional

import aiohttp
import asyncio
import async_timeout

from gehomesdk import (
    GeAuthFailedError,
    GeAuthTermsRequiredError,
    GeNotAuthenticatedError,
    GeGeneralServerError,
    GeSmartHqLogin,
    LOGIN_REGIONS
)
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, CONF_REGION
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN,
    VALIDATE_DATA_TIMEOUT,
    CONFIG_FLOW_VERSION,
    CONF_REFRESH_TOKEN,
    CONF_DEVICE_IDENTIFIER,
    DEVICE_IDENTIFIER_SERIAL_OR_MAC,
    DEVICE_IDENTIFIER_MAC_OR_SERIAL,
    DEFAULT_DEVICE_IDENTIFIER_EXISTING
)
from .exceptions import HaAuthError

_LOGGER = logging.getLogger(__name__)

CONF_MFA_CODE = "mfa_code"
CONF_MFA_RESEND = "resend_code"

def _normalize_username(username: Optional[str]) -> str:
    """Trim whitespace and lowercase the username."""
    if username is None or username.strip() == "":
        raise HaAuthError("Username is required")
    return username.strip().lower()

def _normalize_password(password: Optional[str]) -> str:
    """Trim whitespace from password."""
    if password is None or password.strip() == "":
        raise HaAuthError("Password is required")
    return password.strip()

def _normalize_region(region: Optional[str]) -> str:
    """Ensure valid region."""
    if region is None or not region.upper() in LOGIN_REGIONS.keys():
        raise HaAuthError("Invalid region")
    return region.upper()

def _pick_mfa_method(methods: List[str]) -> str:
    """Prefer email (the only interactive method we currently drive)."""
    return "email" if "email" in methods else (methods[0] if methods else "email")

def _get_user_schema(user_input: Optional[Dict] = None) -> vol.Schema:
    """Return the user step schema, prefilled with previous input if available."""
    user_input = user_input or {}
    return vol.Schema(
        {
            vol.Required(CONF_USERNAME, default=user_input.get(CONF_USERNAME, "")): str,
            vol.Required(CONF_PASSWORD, default=user_input.get(CONF_PASSWORD, "")): str,
            vol.Required(CONF_REGION, default=user_input.get(CONF_REGION, "")): vol.In(LOGIN_REGIONS.keys())
        }
    )

class GeHomeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for GE Home."""

    VERSION = CONFIG_FLOW_VERSION
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_PUSH

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> "GeHomeOptionsFlow":
        """Get the options flow for this handler."""
        return GeHomeOptionsFlow()

    def __init__(self) -> None:
        self._login: Optional[GeSmartHqLogin] = None
        self._pending: Dict[str, str] = {}
        self._mfa_method: str = "email"
        self._last_error: Optional[str] = None
        self._reauth_entry: Optional[config_entries.ConfigEntry] = None

    async def async_step_user(self, user_input: Optional[Dict] = None):
        """Handle the initial step."""
        if user_input:
            try:
                username = _normalize_username(user_input.get(CONF_USERNAME))
            except HaAuthError:
                return self.async_show_form(
                    step_id="user", data_schema=_get_user_schema(user_input),
                    errors={"base": "invalid_auth"})

            # test uniqueness and abort if not unique
            await self.async_set_unique_id(username)
            self._abort_if_unique_id_configured()

            return await self._async_start_login(user_input, step_id="user")

        return self.async_show_form(step_id="user", data_schema=_get_user_schema())

    async def async_step_reauth(self, user_input: Optional[dict] = None):
        """Handle re-auth if login is invalid (may require MFA)."""
        if self._reauth_entry is None:
            self._reauth_entry = self.hass.config_entries.async_get_entry(
                self.context.get("entry_id", ""))

        if user_input is None:
            prefill = {}
            if self._reauth_entry:
                prefill = {
                    CONF_USERNAME: self._reauth_entry.data.get(CONF_USERNAME, ""),
                    CONF_REGION: self._reauth_entry.data.get(CONF_REGION, ""),
                }
            return self.async_show_form(step_id="reauth", data_schema=_get_user_schema(prefill))

        return await self._async_start_login(user_input, step_id="reauth")

    async def async_step_mfa(self, user_input: Optional[dict] = None):
        """Prompt for the one-time verification code."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            if user_input.get(CONF_MFA_RESEND):
                errors = await self._async_resend_code()
            else:
                code = str(user_input.get(CONF_MFA_CODE, "")).strip()
                if not code:
                    errors["base"] = "invalid_mfa_code"
                else:
                    result = await self._async_submit_mfa(code)
                    if result is not None:
                        return result
                    errors["base"] = self._last_error or "invalid_mfa_code"

        return self.async_show_form(
            step_id="mfa",
            data_schema=vol.Schema({
                vol.Optional(CONF_MFA_CODE, default=""): str,
                vol.Optional(CONF_MFA_RESEND, default=False): bool,
            }),
            errors=errors,
        )

    # region internals

    async def _async_start_login(self, user_input: dict, *, step_id: str):
        """Submit credentials; either finish, branch to MFA, or show an error."""
        errors: Dict[str, str] = {}
        try:
            username = _normalize_username(user_input.get(CONF_USERNAME))
            password = _normalize_password(user_input.get(CONF_PASSWORD))
            region = _normalize_region(user_input.get(CONF_REGION))
        except HaAuthError:
            return self.async_show_form(
                step_id=step_id, data_schema=_get_user_schema(user_input),
                errors={"base": "invalid_auth"})

        self._login = GeSmartHqLogin(async_get_clientsession(self.hass))
        self._pending = {CONF_USERNAME: username, CONF_PASSWORD: password, CONF_REGION: region}

        try:
            async with async_timeout.timeout(VALIDATE_DATA_TIMEOUT):
                result = await self._login.async_login(username, password, region)
        except (asyncio.TimeoutError, aiohttp.ClientError):
            errors["base"] = "cannot_connect"
        except GeAuthTermsRequiredError:
            errors["base"] = "terms_required"
        except (GeAuthFailedError, GeNotAuthenticatedError):
            errors["base"] = "invalid_auth"
        except GeGeneralServerError:
            errors["base"] = "cannot_connect"
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Unexpected error during login for %s", username)
            errors["base"] = "unknown"
        else:
            if result.mfa_required:
                self._mfa_method = _pick_mfa_method(result.mfa_methods)
                send_errors = await self._async_resend_code()
                if send_errors:
                    return self.async_show_form(
                        step_id=step_id, data_schema=_get_user_schema(user_input),
                        errors=send_errors)
                return await self.async_step_mfa()
            return self._async_finish(result.token)

        return self.async_show_form(
            step_id=step_id, data_schema=_get_user_schema(user_input), errors=errors)

    async def _async_resend_code(self) -> Dict[str, str]:
        """(Re)send the verification code. Returns an errors dict (empty on success)."""
        if not self._login:
            return {"base": "unknown"}
        try:
            async with async_timeout.timeout(VALIDATE_DATA_TIMEOUT):
                await self._login.async_send_code(self._mfa_method)
        except (asyncio.TimeoutError, aiohttp.ClientError):
            return {"base": "cannot_connect"}
        except GeGeneralServerError:
            return {"base": "cannot_connect"}
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Error sending MFA code")
            return {"base": "unknown"}
        return {}

    async def _async_submit_mfa(self, code: str):
        """Submit the code. Returns a flow result on success, else None."""
        self._last_error = None
        if not self._login:
            self._last_error = "unknown"
            return None
        try:
            async with async_timeout.timeout(VALIDATE_DATA_TIMEOUT):
                token = await self._login.async_submit_code(code)
        except (asyncio.TimeoutError, aiohttp.ClientError):
            self._last_error = "cannot_connect"
            return None
        except GeGeneralServerError:
            self._last_error = "cannot_connect"
            return None
        except (GeAuthFailedError, GeNotAuthenticatedError):
            self._last_error = "invalid_mfa_code"
            return None
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Unexpected error verifying MFA code")
            self._last_error = "unknown"
            return None
        return self._async_finish(token)

    def _async_finish(self, token: Optional[dict]):
        """Persist credentials (incl. refresh token) and create/update the entry."""
        data = dict(self._pending)
        refresh_token = (token or {}).get("refresh_token")
        if refresh_token:
            data[CONF_REFRESH_TOKEN] = refresh_token
        else:
            _LOGGER.warning("No refresh token returned; reconnects may require re-auth")

        if self._reauth_entry:
            self.hass.config_entries.async_update_entry(self._reauth_entry, data=data)
            self.hass.async_create_task(
                self.hass.config_entries.async_reload(self._reauth_entry.entry_id))
            return self.async_abort(reason="reauth_successful")

        return self.async_create_entry(title=self._pending[CONF_USERNAME], data=data)

    # endregion


class GeHomeOptionsFlow(config_entries.OptionsFlow):
    """Handle options for GE Home (post-install configuration)."""

    async def async_step_init(self, user_input: Optional[Dict] = None):
        """Manage the device identifier option."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.options.get(
            CONF_DEVICE_IDENTIFIER, DEFAULT_DEVICE_IDENTIFIER_EXISTING
        )

        options_schema = vol.Schema(
            {
                vol.Required(
                    CONF_DEVICE_IDENTIFIER, default=current
                ): vol.In(
                    [
                        DEVICE_IDENTIFIER_SERIAL_OR_MAC,
                        DEVICE_IDENTIFIER_MAC_OR_SERIAL,
                    ]
                )
            }
        )

        return self.async_show_form(step_id="init", data_schema=options_schema)
