"""Tests for BirdDog Play API client using unittest.IsolatedAsyncioTestCase."""

import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Mock homeassistant modules so tests run in lightweight environments
for mod in [
    "homeassistant",
    "homeassistant.config_entries",
    "homeassistant.const",
    "homeassistant.core",
    "homeassistant.data_entry_flow",
    "homeassistant.helpers",
    "homeassistant.helpers.aiohttp_client",
    "homeassistant.helpers.entity",
    "homeassistant.helpers.entity_platform",
    "homeassistant.helpers.update_coordinator",
    "homeassistant.components",
    "homeassistant.components.sensor",
    "homeassistant.components.select",
    "homeassistant.components.switch",
]:
    sys.modules.setdefault(mod, MagicMock())

from custom_components.birddog_ndi.birddog_api import (
    BirdDogAPIError,
    BirdDogConnectionError,
    BirdDogDevice,
)


class TestBirdDogDevice(unittest.IsolatedAsyncioTestCase):
    """Test suite for BirdDogDevice client."""

    async def test_birddog_device_init(self):
        """Test BirdDog device initialization."""
        device = BirdDogDevice(host="192.168.1.50", port=8080)
        self.assertEqual(device.host, "192.168.1.50")
        self.assertEqual(device.port, 8080)
        self.assertEqual(device.base_url, "http://192.168.1.50:8080")

    async def test_birddog_device_info_parsing(self):
        """Test parsing of device info endpoint."""
        device = BirdDogDevice(host="192.168.1.50", port=8080)

        mock_about_response = {
            "DeviceName": "Stage-Play-01",
            "Model": "PLAY",
            "Version": "v4.5.1",
            "Serial": "BDPLAY12345",
        }

        with patch.object(device, "_request", AsyncMock(return_value=mock_about_response)):
            info = await device.get_device_info()
            self.assertEqual(info["DeviceName"], "Stage-Play-01")
            self.assertEqual(info["Model"], "PLAY")
            self.assertEqual(info["Version"], "v4.5.1")

    async def test_birddog_current_source(self):
        """Test getting current NDI source."""
        device = BirdDogDevice(host="192.168.1.50", port=8080)

        mock_source = {"sourceName": "CAM-01 (Main Camera)"}

        with patch.object(device, "_request", AsyncMock(return_value=mock_source)):
            source_data = await device.get_current_source()
            self.assertEqual(source_data["sourceName"], "CAM-01 (Main Camera)")

    async def test_birddog_set_source(self):
        """Test setting NDI source via POST."""
        device = BirdDogDevice(host="192.168.1.50", port=8080)

        mock_request = AsyncMock(return_value={"status": "ok"})
        with patch.object(device, "_request", mock_request):
            result = await device.set_source("PROPRESENTER (Lyrics)")
            self.assertTrue(result)
            mock_request.assert_called_once_with(
                "POST",
                "/connectTo",
                json_data={"sourceName": "PROPRESENTER (Lyrics)"},
            )

    async def test_birddog_fetch_all_data(self):
        """Test fetching all data aggregate."""
        device = BirdDogDevice(host="192.168.1.50", port=8080)

        with patch.object(
            device,
            "get_device_info",
            AsyncMock(return_value={"DeviceName": "Auditorium-Play", "Version": "v1.2"}),
        ), patch.object(
            device,
            "get_current_source",
            AsyncMock(return_value={"sourceName": "SWITCHER (Program)"}),
        ), patch.object(
            device,
            "get_available_sources",
            AsyncMock(return_value=["SWITCHER (Program)", "PROPRESENTER (Lyrics)"]),
        ), patch.object(
            device,
            "get_audio_mute",
            AsyncMock(return_value=False),
        ):
            data = await device.fetch_all_data()
            self.assertTrue(data["online"])
            self.assertEqual(data["device_name"], "Auditorium-Play")
            self.assertEqual(data["current_source"], "SWITCHER (Program)")
            self.assertEqual(len(data["available_sources"]), 2)
            self.assertFalse(data["audio_muted"])


if __name__ == "__main__":
    unittest.main()
