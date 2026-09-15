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


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BirdDog select entities."""
    coordinator: BirdDogDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([BirdDogSourceSelect(coordinator, entry)])


class BirdDogSourceSelect(CoordinatorEntity[BirdDogDataUpdateCoordinator], SelectEntity):
    """Selector for active NDI video source."""

    _attr_has_entity_name = True
    _attr_name = "Video Source"
    _attr_icon = "mdi:video-switch"

    def __init__(
        self,
        coordinator: BirdDogDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{coordinator.device.host}_video_source"

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
        if current and current not in ("Unknown", "No Source", "None") and current not in sources:
            sources.insert(0, current)
        return sources or ([current] if current else ["No Source"])

    async def async_select_option(self, option: str) -> None:
        """Change the active NDI video source."""
        _LOGGER.info("User switching active NDI source to: %s", option)
        try:
            await self.coordinator.device.set_source(option)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to set NDI source to %s: %s", option, err)
            raise
