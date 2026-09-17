"""Config flow for BirdDog NDI integration (Play, Play Pro, Mini, Flex, Studio)."""

from __future__ import annotations

import logging
import re
import socket
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


GENERIC_DEVICE_NAMES = {
    "birddog",
    "birddogdevice",
    "birddogplay",
    "birddogplaypro",
    "birddogmini",
    "birddogflex",
    "birddogflex4k",
    "birddogstudio",
}


def _normalize_name(val: str | None) -> str:
    """Normalize service name, device name, or hostname to alphanumeric lowercase."""
    if not val:
        return ""
    s = val.split("._")[0].split(".local")[0].strip()
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _extract_discovery_info(discovery_info: Any) -> dict[str, Any]:
    """Extract candidate IPs, hostnames, names, and MAC addresses from ZeroconfServiceInfo."""
    ips: set[str] = set()
    hosts: set[str] = set()

    # 1. Host field
    raw_host = getattr(discovery_info, "host", None)
    if raw_host:
        h = str(raw_host).strip().lower().rstrip(".")
        if h:
            hosts.add(h)
            if "%" in h:
                # Strip IPv6 interface scope
                clean_ip = h.split("%")[0]
                ips.add(clean_ip)
            elif ":" in h and not h.startswith("fe80") and h.count(":") == 1:
                # IPv4 with port
                ips.add(h.split(":")[0])
                hosts.add(h.split(":")[0])
            else:
                ips.add(h)

    # 2. ip_address field
    ip_addr = getattr(discovery_info, "ip_address", None)
    if ip_addr:
        s = str(ip_addr).strip().lower().split("%")[0]
        if s:
            ips.add(s)

    # 3. ip_addresses & addresses lists
    for attr in ("ip_addresses", "addresses"):
        addrs = getattr(discovery_info, attr, None)
        if addrs and isinstance(addrs, (list, tuple, set)):
            for a in addrs:
                s = str(a).strip().lower().split("%")[0]
                if s:
                    ips.add(s)

    # 4. Hostname
    hostname = getattr(discovery_info, "hostname", None)
    raw_hostname = ""
    if hostname:
        raw_hostname = str(hostname).strip().lower().rstrip(".")
        if raw_hostname:
            hosts.add(raw_hostname)

    # 5. Service Name (e.g. BirdDog-PLAY-94F8._http._tcp.local.)
    raw_name = getattr(discovery_info, "name", "") or ""
    clean_service_name = raw_name.split("._")[0].split(".local")[0].strip()

    # 6. TXT Properties
    props = getattr(discovery_info, "properties", {}) or {}
    mac = ""
    for mac_key in ("mac", "macaddress", "mac_address", "ethmac", "ethernetmac"):
        if mac_key in props:
            val = props[mac_key]
            if isinstance(val, bytes):
                try:
                    val = val.decode("utf-8")
                except Exception:
                    val = val.hex()
            mac = str(val).strip().lower().replace(":", "").replace("-", "")
            break

    return {
        "ips": ips,
        "hosts": hosts,
        "hostname": raw_hostname,
        "name": clean_service_name,
        "mac": mac,
    }


def _extract_entry_info(
    entry: config_entries.ConfigEntry,
    hass: Any = None,
) -> dict[str, Any]:
    """Extract candidate IPs, hostnames, titles, and MAC addresses from a ConfigEntry."""
    ips: set[str] = set()
    hosts: set[str] = set()

    entry_host = str(entry.data.get(CONF_HOST, "")).strip().lower().rstrip(".")
    if entry_host:
        hosts.add(entry_host)
        if "%" in entry_host:
            clean_host = entry_host.split("%")[0]
            ips.add(clean_host)
        elif ":" in entry_host and not entry_host.startswith("fe80") and entry_host.count(":") == 1:
            clean_host = entry_host.split(":")[0]
            ips.add(clean_host)
            hosts.add(clean_host)
        else:
            ips.add(entry_host)

    uid = str(entry.unique_id or "").strip().lower().rstrip(".")
    if uid:
        hosts.add(uid)
        if ":" in uid and not uid.startswith("fe80") and uid.count(":") == 1:
            clean_uid = uid.split(":")[0]
            ips.add(clean_uid)
            hosts.add(clean_uid)
        else:
            ips.add(uid)

    title = str(entry.title or "").strip()
    conf_name = str(entry.data.get(CONF_NAME, "")).strip()

    mac = ""
    serial = ""
    if hass and hasattr(hass, "data") and DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
        coord = hass.data[DOMAIN][entry.entry_id]
        if getattr(coord, "data", None) and isinstance(coord.data, dict):
            c_data = coord.data
            c_ip = str(c_data.get("ip_address", "")).strip().lower()
            if c_ip:
                ips.add(c_ip)
            c_host = str(c_data.get("host", "")).strip().lower()
            if c_host:
                hosts.add(c_host)
                ips.add(c_host)
            c_mac = str(c_data.get("mac_address", "")).strip().lower().replace(":", "").replace("-", "")
            if c_mac and c_mac != "unknown":
                mac = c_mac
            c_serial = str(c_data.get("serial", "")).strip().lower()
            if c_serial:
                serial = c_serial

    return {
        "ips": ips,
        "hosts": hosts,
        "title": title,
        "name": conf_name,
        "mac": mac,
        "serial": serial,
        "unique_id": uid,
    }


def _is_match(
    disc: dict[str, Any],
    entry_info: dict[str, Any],
    resolved_disc_ips: set[str] | None = None,
    resolved_entry_ips: set[str] | None = None,
) -> bool:
    """Determine if a discovered device matches an existing configured entry."""
    disc_all_ips = set(disc["ips"])
    if resolved_disc_ips:
        disc_all_ips |= resolved_disc_ips

    entry_all_ips = set(entry_info["ips"])
    if resolved_entry_ips:
        entry_all_ips |= resolved_entry_ips

    # 1. IP address match
    if disc_all_ips & entry_all_ips:
        return True

    # 2. Hostname match
    if disc["hosts"] & entry_info["hosts"]:
        return True

    # 3. MAC address match
    disc_mac = disc.get("mac", "").replace(":", "").replace("-", "")
    entry_mac = entry_info.get("mac", "").replace(":", "").replace("-", "")
    if disc_mac and entry_mac and disc_mac == entry_mac:
        return True

    # 4. Unique ID match
    uid = entry_info.get("unique_id", "")
    if uid:
        if uid in disc_all_ips or uid in disc["hosts"]:
            return True
        if any(uid.startswith(f"{h}:") or h.startswith(f"{uid}:") for h in disc["hosts"]):
            return True

    # 5. Specific Hardware Name / MAC Suffix match
    disc_norm = _normalize_name(disc.get("name"))
    disc_host_norm = _normalize_name(disc.get("hostname"))
    entry_title_norm = _normalize_name(entry_info.get("title"))
    entry_name_norm = _normalize_name(entry_info.get("name"))

    for d_name in (disc_norm, disc_host_norm):
        if d_name and d_name not in GENERIC_DEVICE_NAMES:
            if d_name in (entry_title_norm, entry_name_norm):
                return True
            # Match 4-hex hardware suffix (e.g. 94f8)
            if len(d_name) >= 4:
                suffix = d_name[-4:]
                if all(c in "0123456789abcdef" for c in suffix):
                    if entry_mac and entry_mac.endswith(suffix):
                        return True
                    if entry_title_norm.endswith(suffix) or entry_name_norm.endswith(suffix):
                        return True

    return False


def _is_device_already_configured(
    entries: list[config_entries.ConfigEntry],
    host: str,
    hostname: str | None = None,
    addresses: list[Any] | None = None,
    name: str | None = None,
    hass: Any = None,
    discovery_info: Any = None,
) -> bool:
    """Comprehensive check if a device is already configured across all existing entries."""
    if discovery_info is not None:
        disc = _extract_discovery_info(discovery_info)
    else:
        disc = {
            "ips": {host.strip().lower().split(":")[0]},
            "hosts": {host.strip().lower(), host.strip().lower().split(":")[0]},
            "hostname": (hostname or "").strip().lower().rstrip("."),
            "name": name or "",
            "mac": "",
        }
        if addresses:
            for a in addresses:
                s = str(a).strip().lower().split("%")[0]
                disc["ips"].add(s)
                disc["hosts"].add(s)

    # 1. Fast pass: Match directly on declared IPs, hosts, MAC, unique_ids, or titles
    for entry in entries:
        entry_info = _extract_entry_info(entry, hass=hass)
        if _is_match(disc, entry_info):
            return True

    # 2. Slow pass: If not matched and hostname needs resolution, resolve candidates
    resolved_disc_ips: set[str] = set()
    if disc.get("hostname"):
        try:
            addr_info = socket.getaddrinfo(disc["hostname"], None)
            for res in addr_info:
                resolved_disc_ips.add(res[4][0].strip().lower())
        except Exception:
            pass

    for entry in entries:
        entry_info = _extract_entry_info(entry, hass=hass)
        resolved_entry_ips: set[str] = set()
        entry_host = entry.data.get(CONF_HOST)
        if entry_host and not entry_host.replace(".", "").isdigit():
            try:
                addr_info = socket.getaddrinfo(entry_host, None)
                for res in addr_info:
                    resolved_entry_ips.add(res[4][0].strip().lower())
            except Exception:
                pass

        if _is_match(disc, entry_info, resolved_disc_ips, resolved_entry_ips):
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
        if not hasattr(self, "context") or self.context is None:
            self.context = {}

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
            if _is_device_already_configured(
                self._async_current_entries(),
                host=host,
                name=name,
                hass=getattr(self, "hass", None),
            ):
                return self.async_abort(reason="already_configured")

            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            device = BirdDogDevice(host=host, port=port, password=password, session=session)

            try:
                await device.test_connection()
                info = await device.get_device_info()
                title = info.get("DeviceName") or info.get("MyHostName") or name
                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_HOST: host,
                        CONF_PORT: device.port,
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

        # 1. Abort immediately if device is already configured in any existing entry
        if _is_device_already_configured(
            self._async_current_entries(),
            host=host,
            hostname=discovery_info.hostname,
            name=discovery_info.name,
            hass=getattr(self, "hass", None),
            discovery_info=discovery_info,
        ):
            return self.async_abort(reason="already_configured")

        disc = _extract_discovery_info(discovery_info)

        # 2. Abort if another flow is already in progress for this same device
        if hasattr(self, "_async_in_progress"):
            my_flow_id = getattr(self, "flow_id", None)
            current_flows = self._async_in_progress(include_uninitialized=True)
            for flow in current_flows:
                flow_id = flow.get("flow_id")
                if my_flow_id and flow_id == my_flow_id:
                    continue
                flow_ctx = flow.get("context", {})
                flow_ph = flow_ctx.get("title_placeholders", {})
                flow_host = str(flow_ph.get("host", "")).strip().lower()
                flow_name = str(flow_ph.get("name", "")).strip().lower()
                if flow_host and flow_host in disc["hosts"]:
                    return self.async_abort(reason="already_in_progress")
                if flow_name and _normalize_name(flow_name) == _normalize_name(disc["name"]):
                    if _normalize_name(flow_name) not in GENERIC_DEVICE_NAMES:
                        return self.async_abort(reason="already_in_progress")

        # Set unique_id to canonical identifier (MAC address, or hostname, or host)
        canonical_uid = disc["mac"] or disc["hostname"] or host
        await self.async_set_unique_id(canonical_uid)
        self._abort_if_unique_id_configured(updates={CONF_HOST: host})

        # Zeroconf _http._tcp announces web server port (80), but BirdDog REST API is on 8080
        effective_port = DEFAULT_PORT if port == 80 else port
        self._discovered_host = host
        self._discovered_port = effective_port
        raw_name = discovery_info.name or "BirdDog Device"
        self._discovered_name = raw_name.split(".")[0].replace("_", " ").title()

        if not hasattr(self, "context") or self.context is None:
            self.context = {}
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
                info = await device.get_device_info()
                title = (
                    info.get("DeviceName")
                    or info.get("MyHostName")
                    or self._discovered_name
                )
                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_HOST: self._discovered_host,
                        CONF_PORT: device.port,
                        CONF_PASSWORD: password,
                        CONF_NAME: title,
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
