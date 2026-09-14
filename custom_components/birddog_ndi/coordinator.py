"""DataUpdateCoordinator for the BirdDog Play NDI integration."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .birddog_api import BirdDogConnectionError, BirdDogDevice
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class BirdDogDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching data from BirdDog device."""

    def __init__(
        self,
        hass: HomeAssistant,
        device: BirdDogDevice,
        update_interval: int = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        """Initialize the coordinator."""
        self.device = device
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{device.host}",
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from BirdDog device."""
        try:
            return await self.device.fetch_all_data()
        except BirdDogConnectionError as err:
            raise UpdateFailed(f"Error communicating with BirdDog {self.device.host}: {err}") from err
