"""Config flow for BirdDog NDI integration (Play, Play Pro, Mini, Flex, Studio)."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from .birddog_api import BirdDogAuthError, BirdDogConnectionError, BirdDogDevice
from .const import (
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    DEFAULT_NAME,
    DEFAULT_PASSWORD,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def get_user_data_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Generate user data schema with optional default values."""
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=defaults.get(CONF_HOST, "")): str,
            vol.Optional(CONF_PORT, default=defaults.get(CONF_PORT, DEFAULT_PORT)): int,
            vol.Optional(CONF_PASSWORD, default=defaults.get(CONF_PASSWORD, DEFAULT_PASSWORD)): str,
            vol.Optional(CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)): str,
        }
    )


def _is_device_already_configured(
    entries: list[config_entries.ConfigEntry],
    host: str,
    hostname: str | None = None,
    addresses: list[Any] | None = None,
) -> bool:
    """Check if a device is already configured across all existing entries."""
    candidates = {host.strip().lower(), host.strip().split(":")[0].lower()}
    if hostname:
        clean_hostname = hostname.strip().lower().rstrip(".")
        candidates.add(clean_hostname)
        candidates.add(hostname.strip().lower())
    if addresses:
        for addr in addresses:
            addr_str = str(addr).strip().lower()
            candidates.add(addr_str)
            candidates.add(addr_str.split(":")[0])

    for entry in entries:
        entry_host = str(entry.data.get(CONF_HOST, "")).strip().lower()
        if entry_host in candidates:
            return True
        entry_uid = str(entry.unique_id or "").strip().lower()
        if any(c == entry_uid or entry_uid.startswith(f"{c}:") or c in entry_uid for c in candidates):
            return True
    return False


class BirdDogConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BirdDog NDI devices."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_host: str | None = None
        self._discovered_port: int = DEFAULT_PORT
        self._discovered_name: str = DEFAULT_NAME

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle manual setup."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input.get(CONF_PORT, DEFAULT_PORT)
            password = user_input.get(CONF_PASSWORD, DEFAULT_PASSWORD).strip()
            name = user_input.get(CONF_NAME, DEFAULT_NAME).strip()

            # Abort if device is already configured in any existing entry
            if _is_device_already_configured(self._async_current_entries(), host):
                return self.async_abort(reason="already_configured")

            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            device = BirdDogDevice(host=host, port=port, password=password, session=session)

            try:
                await device.test_connection()
                info = await device.get_device_info()
                title = info.get("DeviceName") or name
                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                        CONF_PASSWORD: password,
                        CONF_NAME: title,
                    },
                )
            except BirdDogAuthError:
                errors["base"] = "invalid_auth"
            except BirdDogConnectionError:
                errors["base"] = "cannot_connect"
            except Exception as ex:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception configuring BirdDog: %s", ex)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=get_user_data_schema(user_input),
            errors=errors,
        )

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> FlowResult:
        """Handle Zeroconf / mDNS auto-discovery with strict device filtering."""
        name = (discovery_info.name or "").lower()
        hostname = (discovery_info.hostname or "").lower()
        host = str(discovery_info.host)
        port = discovery_info.port or DEFAULT_PORT

        # Validate that this is a recognized BirdDog hardware family
        valid_keywords = ("birddog", "play", "mini", "flex", "studio")
        if not any(k in name or k in hostname for k in valid_keywords):
            return self.async_abort(reason="not_birddog")

        # Collect all candidate IP addresses and hostnames from discovery
        addresses = []
        if hasattr(discovery_info, "ip_address") and discovery_info.ip_address:
            addresses.append(str(discovery_info.ip_address))
        if hasattr(discovery_info, "addresses") and discovery_info.addresses:
            addresses.extend(str(a) for a in discovery_info.addresses)

        # Abort immediately if device is already configured
        if _is_device_already_configured(
            self._async_current_entries(),
            host=host,
            hostname=discovery_info.hostname,
            addresses=addresses,
        ):
            return self.async_abort(reason="already_configured")

        await self.async_set_unique_id(host)
        self._abort_if_unique_id_configured()

        self._discovered_host = host
        self._discovered_port = port
        raw_name = discovery_info.name or "BirdDog Device"
        self._discovered_name = raw_name.split(".")[0].replace("_", " ").title()

        self.context["title_placeholders"] = {
            "name": self._discovered_name,
            "host": host,
        }
        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm discovery and validate connection."""
        errors: dict[str, str] = {}

        # Abort immediately before showing the form if already configured
        if self._discovered_host and _is_device_already_configured(
            self._async_current_entries(),
            host=self._discovered_host,
        ):
            return self.async_abort(reason="already_configured")

        if user_input is not None:

            password = user_input.get(CONF_PASSWORD, DEFAULT_PASSWORD).strip()
            session = async_get_clientsession(self.hass)
            device = BirdDogDevice(
                host=self._discovered_host,
                port=self._discovered_port,
                password=password,
                session=session,
            )

            try:
                await device.test_connection()
                return self.async_create_entry(
                    title=self._discovered_name,
                    data={
                        CONF_HOST: self._discovered_host,
                        CONF_PORT: self._discovered_port,
                        CONF_PASSWORD: password,
                        CONF_NAME: self._discovered_name,
                    },
                )
            except BirdDogAuthError:
                errors["base"] = "invalid_auth"
            except BirdDogConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"

        schema = vol.Schema(
            {
                vol.Required(CONF_PASSWORD, default=DEFAULT_PASSWORD): str,
            }
        )

        return self.async_show_form(
            step_id="zeroconf_confirm",
            data_schema=schema,
            description_placeholders={
                "name": self._discovered_name,
                "host": self._discovered_host,
            },
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create options flow handler."""
        return BirdDogOptionsFlowHandler(config_entry)


class BirdDogOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle BirdDog options changes."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data = self.config_entry.data
        options = self.config_entry.options

        current_password = options.get(CONF_PASSWORD, data.get(CONF_PASSWORD, DEFAULT_PASSWORD))
        current_interval = options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        schema = vol.Schema(
            {
                vol.Required(CONF_PASSWORD, default=current_password): str,
                vol.Optional(CONF_SCAN_INTERVAL, default=current_interval): vol.All(
                    vol.Coerce(int), vol.Range(min=5, max=60)
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
