"""Switch platform for BirdDog Play NDI."""

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
    """Set up BirdDog switch entities."""
    coordinator: BirdDogDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            BirdDogAudioMuteSwitch(coordinator, entry),
            BirdDogTallySwitch(coordinator, entry),
        ]
    )


class BirdDogBaseSwitch(CoordinatorEntity[BirdDogDataUpdateCoordinator], SwitchEntity):
    """Base class for BirdDog switches."""

    def __init__(
        self,
        coordinator: BirdDogDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the switch entity."""
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


class BirdDogAudioMuteSwitch(BirdDogBaseSwitch):
    """Switch for audio mute."""

    _attr_name = "Audio Mute"
    _attr_icon = "mdi:volume-mute"

    def __init__(
        self,
        coordinator: BirdDogDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.device.host}_audio_mute"

    @property
    def is_on(self) -> bool:
        """Return True if audio is muted."""
        if not self.coordinator.data:
            return False
        return bool(self.coordinator.data.get("audio_muted", False))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Mute audio."""
        success = await self.coordinator.device.set_audio_mute(True)
        if success:
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Unmute audio."""
        success = await self.coordinator.device.set_audio_mute(False)
        if success:
            await self.coordinator.async_request_refresh()


class BirdDogTallySwitch(BirdDogBaseSwitch):
    """Switch for Tally light indicator."""

    _attr_name = "Tally Light"
    _attr_icon = "mdi:alarm-light"

    def __init__(
        self,
        coordinator: BirdDogDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.device.host}_tally"

    @property
    def is_on(self) -> bool:
        """Return True if tally light is on."""
        if not self.coordinator.data:
            return False
        return bool(self.coordinator.data.get("tally_on", False))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn tally light on."""
        success = await self.coordinator.device.set_tally(True)
        if success:
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn tally light off."""
        success = await self.coordinator.device.set_tally(False)
        if success:
            await self.coordinator.async_request_refresh()
