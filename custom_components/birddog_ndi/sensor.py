"""Sensor platform for BirdDog Play NDI."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_MODEL, DOMAIN, MANUFACTURER
from .coordinator import BirdDogDataUpdateCoordinator

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="status",
        name="Status",
        icon="mdi:check-network",
    ),
    SensorEntityDescription(
        key="current_source",
        name="Current NDI Source",
        icon="mdi:video-input-antenna",
    ),
    SensorEntityDescription(
        key="source_ip",
        name="Source IP",
        icon="mdi:ip-network-outline",
    ),
    SensorEntityDescription(
        key="source_port",
        name="Source Port",
        icon="mdi:numeric",
    ),
    SensorEntityDescription(
        key="failover_source",
        name="Failover NDI Source",
        icon="mdi:video-switch-outline",
    ),
    SensorEntityDescription(
        key="video_format",
        name="Video Format",
        icon="mdi:television-box",
    ),
    SensorEntityDescription(
        key="bitrate",
        name="Decode Bitrate",
        icon="mdi:speedometer",
    ),
    SensorEntityDescription(
        key="transport",
        name="Transport Protocol",
        icon="mdi:transit-connection-variant",
    ),
    SensorEntityDescription(
        key="screensaver",
        name="Screen Saver Mode",
        icon="mdi:image-filter-frames",
    ),
    SensorEntityDescription(
        key="ip_address",
        name="IP Address",
        icon="mdi:ip-network",
    ),
    SensorEntityDescription(
        key="mac_address",
        name="MAC Address",
        icon="mdi:network",
    ),
    SensorEntityDescription(
        key="firmware",
        name="Firmware Version",
        icon="mdi:chip",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BirdDog sensor entities based on a config entry."""
    coordinator: BirdDogDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        BirdDogSensor(coordinator, entry, description)
        for description in SENSOR_TYPES
    ]
    async_add_entities(entities)


class BirdDogSensor(CoordinatorEntity[BirdDogDataUpdateCoordinator], SensorEntity):
    """Representation of a BirdDog sensor."""

    def __init__(
        self,
        coordinator: BirdDogDataUpdateCoordinator,
        entry: ConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{coordinator.device.host}_{description.key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this BirdDog unit."""
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
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        key = self.entity_description.key
        if key == "status":
            return "online" if self.coordinator.data.get("online") else "offline"
        if key == "current_source":
            return self.coordinator.data.get("current_source")
        if key == "source_ip":
            return self.coordinator.data.get("source_ip")
        if key == "source_port":
            return self.coordinator.data.get("source_port")
        if key == "failover_source":
            return self.coordinator.data.get("failover_source")
        if key == "video_format":
            return self.coordinator.data.get("video_format")
        if key == "bitrate":
            return self.coordinator.data.get("bitrate")
        if key == "transport":
            return self.coordinator.data.get("transport")
        if key == "screensaver":
            return self.coordinator.data.get("screensaver")
        if key == "ip_address":
            return self.coordinator.data.get("host")
        if key == "mac_address":
            return self.coordinator.data.get("mac_address")
        if key == "firmware":
            return self.coordinator.data.get("firmware")
        return None
