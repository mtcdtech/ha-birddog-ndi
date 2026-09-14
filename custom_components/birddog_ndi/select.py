"""Select platform for BirdDog Play NDI video source switching."""

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
    """Set up the BirdDog video source select entity."""
    coordinator: BirdDogDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([BirdDogSourceSelect(coordinator, entry)])


class BirdDogSourceSelect(CoordinatorEntity[BirdDogDataUpdateCoordinator], SelectEntity):
    """Representation of an NDI video source selector for BirdDog."""

    _attr_has_entity_name = True
    _attr_name = "Video Source"
    _attr_icon = "mdi:video-switch"

    def __init__(
        self,
        coordinator: BirdDogDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the select entity."""
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
        sources = self.coordinator.data.get("available_sources", [])
        current = self.current_option
        if current and current != "Unknown" and current not in sources:
            return [current] + sources
        return sources or ([current] if current else ["None"])

    async def async_select_option(self, option: str) -> None:
        """Change the NDI video source on the BirdDog device."""
        _LOGGER.info("User requested NDI source change to: %s", option)
        try:
            await self.coordinator.device.set_source(option)
            # Instantly request an update to refresh state
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to set NDI source to %s: %s", option, err)
            raise
