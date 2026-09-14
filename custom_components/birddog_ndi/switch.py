"""Switch platform for BirdDog Play NDI audio control."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
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
    """Set up the BirdDog audio mute switch entity."""
    coordinator: BirdDogDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([BirdDogAudioMuteSwitch(coordinator, entry)])


class BirdDogAudioMuteSwitch(CoordinatorEntity[BirdDogDataUpdateCoordinator], SwitchEntity):
    """Representation of an audio mute toggle for BirdDog."""

    _attr_has_entity_name = True
    _attr_name = "Audio Mute"
    _attr_icon = "mdi:volume-mute"

    def __init__(
        self,
        coordinator: BirdDogDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{coordinator.device.host}_audio_mute"

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
    def is_on(self) -> bool:
        """Return True if audio is muted."""
        if not self.coordinator.data:
            return False
        return bool(self.coordinator.data.get("audio_muted", False))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Mute audio on the BirdDog device."""
        success = await self.coordinator.device.set_audio_mute(True)
        if success:
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Unmute audio on the BirdDog device."""
        success = await self.coordinator.device.set_audio_mute(False)
        if success:
            await self.coordinator.async_request_refresh()
