"""Binary sensor platform for BirdDog Play NDI."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_MODEL, DOMAIN, MANUFACTURER
from .coordinator import BirdDogDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the BirdDog binary sensor entities."""
    coordinator: BirdDogDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([BirdDogDecodingBinarySensor(coordinator, entry)])


class BirdDogDecodingBinarySensor(
    CoordinatorEntity[BirdDogDataUpdateCoordinator], BinarySensorEntity
):
    """Binary sensor indicating whether BirdDog is actively decoding an NDI stream."""

    _attr_has_entity_name = True
    _attr_name = "Decoding Active"
    _attr_icon = "mdi:play-network"
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(
        self,
        coordinator: BirdDogDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{coordinator.device.host}_decoding_active"

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
        """Return True if the unit is actively decoding an NDI stream."""
        if not self.coordinator.data:
            return False
        return bool(self.coordinator.data.get("is_decoding", False))
