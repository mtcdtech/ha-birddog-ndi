"""The BirdDog Play NDI Home Assistant integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .birddog_api import BirdDogDevice
from .const import (
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    DEFAULT_PASSWORD,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .coordinator import BirdDogDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SELECT,
    Platform.SWITCH,
    Platform.BUTTON,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up BirdDog Play NDI from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    host: str = entry.data[CONF_HOST]
    port: int = entry.data.get(CONF_PORT, DEFAULT_PORT)
    password: str = entry.options.get(
        CONF_PASSWORD, entry.data.get(CONF_PASSWORD, DEFAULT_PASSWORD)
    )
    interval: int = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    session = async_get_clientsession(hass)
    device = BirdDogDevice(host=host, port=port, password=password, session=session)

    coordinator = BirdDogDataUpdateCoordinator(hass, device, update_interval=interval)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Automatically dismiss any pending discovery flows for this device so ghost discovery cards disappear
    if hasattr(hass.config_entries, "flow") and hasattr(hass.config_entries.flow, "async_progress_by_handler"):
        for flow in hass.config_entries.flow.async_progress_by_handler(DOMAIN):
            flow_context = flow.get("context", {})
            flow_host = flow_context.get("title_placeholders", {}).get("host")
            if flow_host:
                clean_flow_host = str(flow_host).strip().lower().split(":")[0]
                if clean_flow_host in (host.strip().lower(), host.strip().split(":")[0].lower()):
                    try:
                        hass.config_entries.flow.async_abort(flow["flow_id"])
                    except Exception as err:
                        _LOGGER.debug("Could not auto-abort flow %s: %s", flow.get("flow_id"), err)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: BirdDogDataUpdateCoordinator = hass.data[DOMAIN].pop(entry.entry_id, None)
        if coordinator:
            await coordinator.device.close()

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
