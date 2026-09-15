"""Sensor platform for BirdDog NDI (Play, Play Pro, Mini, Flex, Studio)."""

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
        key="operation_mode",
        name="Operation Mode",
        icon="mdi:swap-horizontal",
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
        key="network_mode",
        name="Network Mode",
        icon="mdi:cog-network",
    ),
    SensorEntityDescription(
        key="firmware",
        name="Firmware Version",
        icon="mdi:chip",
    ),
    SensorEntityDescription(
        key="model",
        name="Model",
        icon="mdi:devices",
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
        data = self.coordinator.data

        if key == "status":
            return "Online" if data.get("online") else "Offline"
        if key == "current_source":
            return data.get("current_source")
        if key == "operation_mode":
            return data.get("operation_mode")
        if key == "ip_address":
            return data.get("ip_address") or data.get("host")
        if key == "mac_address":
            return data.get("mac_address")
        if key == "network_mode":
            return data.get("network_mode")
        if key == "firmware":
            return data.get("firmware")
        if key == "model":
            return data.get("model")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return device attributes for deeper diagnostics."""
        if not self.coordinator.data:
            return {}

        data = self.coordinator.data
        if self.entity_description.key == "current_source":
            return {
                "is_decoding": data.get("is_decoding", False),
                "available_sources_count": len(data.get("available_sources", [])),
            }
        if self.entity_description.key == "ip_address":
            return {
                "netmask": data.get("netmask"),
                "gateway": data.get("gateway"),
                "port": data.get("port"),
            }
        return {}
