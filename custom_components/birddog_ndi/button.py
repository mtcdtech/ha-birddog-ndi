"""Button platform for BirdDog Play NDI."""

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
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
    """Set up BirdDog button entities."""
    coordinator: BirdDogDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            BirdDogRebootButton(coordinator, entry),
            BirdDogRestartVideoButton(coordinator, entry),
            BirdDogRefreshSourcesButton(coordinator, entry),
        ]
    )


class BirdDogBaseButton(CoordinatorEntity[BirdDogDataUpdateCoordinator], ButtonEntity):
    """Base class for BirdDog buttons."""

    def __init__(
        self,
        coordinator: BirdDogDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the button."""
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


class BirdDogRebootButton(BirdDogBaseButton):
    """Button to reboot the BirdDog device."""

    _attr_name = "Reboot Device"
    _attr_icon = "mdi:restart"
    _attr_device_class = ButtonDeviceClass.RESTART

    def __init__(
        self,
        coordinator: BirdDogDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.device.host}_reboot"

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.warning("User triggered device reboot on BirdDog %s", self.coordinator.device.host)
        await self.coordinator.device.reboot()


class BirdDogRestartVideoButton(BirdDogBaseButton):
    """Button to restart the video decoding subsystem."""

    _attr_name = "Restart Video Engine"
    _attr_icon = "mdi:reload"
    _attr_device_class = ButtonDeviceClass.RESTART

    def __init__(
        self,
        coordinator: BirdDogDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.device.host}_restart_video"

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.info("User triggered video engine restart on BirdDog %s", self.coordinator.device.host)
        await self.coordinator.device.restart_video()
        await self.coordinator.async_request_refresh()


class BirdDogRefreshSourcesButton(BirdDogBaseButton):
    """Button to trigger an NDI source discovery scan."""

    _attr_name = "Refresh NDI Sources"
    _attr_icon = "mdi:refresh"

    def __init__(
        self,
        coordinator: BirdDogDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.device.host}_refresh_sources"

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.info("Refreshing NDI sources on BirdDog %s", self.coordinator.device.host)
        await self.coordinator.device.refresh_sources()
        await self.coordinator.async_request_refresh()
