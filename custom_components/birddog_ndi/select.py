"""Select platform for BirdDog Play NDI."""

from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_MODEL, DOMAIN, MANUFACTURER
from .coordinator import BirdDogDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

SCREENSAVER_MODES = ["Logo", "Black", "ScreenSaver"]
TRANSPORT_PROTOCOLS = ["TCP", "UDP", "Multicast"]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BirdDog select entities."""
    coordinator: BirdDogDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            BirdDogSourceSelect(coordinator, entry),
            BirdDogFailoverSelect(coordinator, entry),
            BirdDogScreensaverSelect(coordinator, entry),
            BirdDogTransportSelect(coordinator, entry),
        ]
    )


class BirdDogBaseSelect(CoordinatorEntity[BirdDogDataUpdateCoordinator], SelectEntity):
    """Base class for BirdDog select entities."""

    def __init__(
        self,
        coordinator: BirdDogDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        data = self.coordinator.data or {}
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.device.host)},
            name=self._entry.title,
            manufacturer=MANUFACTURER,
            model=data.get("model", DEFAULT_MODEL),
            sw_version=data.get("firmware"),
            configuration_url=self.coordinator.device.base_url,
        )


class BirdDogSourceSelect(BirdDogBaseSelect):
    """Selector for active NDI video source."""

    _attr_name = "Video Source"
    _attr_icon = "mdi:video-switch"

    def __init__(
        self,
        coordinator: BirdDogDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.device.host}_video_source"

    @property
    def current_option(self) -> str | None:
        """Return the current selected NDI video source."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("current_source")

    @property
    def options(self) -> list[str]:
        """Return available NDI sources to choose from."""
        if not self.coordinator.data:
            return []
        sources = list(self.coordinator.data.get("available_sources", []))
        current = self.current_option
        if current and current not in ("Unknown", "None") and current not in sources:
            sources.insert(0, current)
        return sources or ([current] if current else ["None"])

    async def async_select_option(self, option: str) -> None:
        """Change the active NDI video source."""
        _LOGGER.info("User switching active NDI source to: %s", option)
        try:
            await self.coordinator.device.set_source(option)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to set NDI source to %s: %s", option, err)
            raise


class BirdDogFailoverSelect(BirdDogBaseSelect):
    """Selector for failover NDI source."""

    _attr_name = "Failover Source"
    _attr_icon = "mdi:video-switch-outline"

    def __init__(
        self,
        coordinator: BirdDogDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.device.host}_failover_source"

    @property
    def current_option(self) -> str | None:
        """Return the current failover source."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("failover_source", "None")

    @property
    def options(self) -> list[str]:
        """Return available sources for failover."""
        if not self.coordinator.data:
            return ["None"]
        sources = ["None"] + list(self.coordinator.data.get("available_sources", []))
        current = self.current_option
        if current and current not in sources:
            sources.append(current)
        return list(dict.fromkeys(sources))

    async def async_select_option(self, option: str) -> None:
        """Change the failover NDI source."""
        _LOGGER.info("User setting failover NDI source to: %s", option)
        try:
            await self.coordinator.device.set_failover_source(option)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to set failover NDI source to %s: %s", option, err)
            raise


class BirdDogScreensaverSelect(BirdDogBaseSelect):
    """Selector for screen saver display mode."""

    _attr_name = "Screen Saver Mode"
    _attr_icon = "mdi:image-filter-frames"

    def __init__(
        self,
        coordinator: BirdDogDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.device.host}_screensaver_mode"

    @property
    def current_option(self) -> str | None:
        """Return the current screensaver mode."""
        if not self.coordinator.data:
            return None
        mode = self.coordinator.data.get("screensaver", "Logo")
        return mode if mode in SCREENSAVER_MODES else SCREENSAVER_MODES[0]

    @property
    def options(self) -> list[str]:
        """Return available screensaver modes."""
        return SCREENSAVER_MODES

    async def async_select_option(self, option: str) -> None:
        """Change the screensaver mode."""
        await self.coordinator.device.set_screensaver(option)
        await self.coordinator.async_request_refresh()


class BirdDogTransportSelect(BirdDogBaseSelect):
    """Selector for decode transport protocol."""

    _attr_name = "Transport Protocol"
    _attr_icon = "mdi:transit-connection-variant"

    def __init__(
        self,
        coordinator: BirdDogDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.device.host}_transport_protocol"

    @property
    def current_option(self) -> str | None:
        """Return the current transport protocol."""
        if not self.coordinator.data:
            return None
        transport = self.coordinator.data.get("transport", "TCP")
        return transport if transport in TRANSPORT_PROTOCOLS else "TCP"

    @property
    def options(self) -> list[str]:
        """Return available transport protocols."""
        return TRANSPORT_PROTOCOLS

    async def async_select_option(self, option: str) -> None:
        """Change the transport protocol."""
        await self.coordinator.device.set_transport(option)
        await self.coordinator.async_request_refresh()
