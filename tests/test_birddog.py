"""Tests for BirdDog Play, Mini, Flex API client using unittest.IsolatedAsyncioTestCase."""

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
    "homeassistant.helpers.service_info",
    "homeassistant.helpers.service_info.zeroconf",
    "homeassistant.helpers.update_coordinator",
    "homeassistant.components",
    "homeassistant.components.sensor",
    "homeassistant.components.binary_sensor",
    "homeassistant.components.select",
    "homeassistant.components.switch",
    "homeassistant.components.button",
]:
    sys.modules.setdefault(mod, MagicMock())

from custom_components.birddog_ndi.birddog_api import (
    BirdDogAPIError,
    BirdDogAuthError,
    BirdDogConnectionError,
    BirdDogDevice,
)


class TestBirdDogDevice(unittest.IsolatedAsyncioTestCase):
    """Test suite for BirdDogDevice client."""

    async def test_birddog_device_init(self):
        """Test BirdDog device initialization."""
        device = BirdDogDevice(host="192.168.1.50", port=8080, password="birddog")
        self.assertEqual(device.host, "192.168.1.50")
        self.assertEqual(device.port, 8080)
        self.assertEqual(device.password, "birddog")
        self.assertEqual(device.base_url, "http://192.168.1.50:8080")

    async def test_birddog_mini_open_api_no_auth_needed(self):
        """Test BirdDog Mini with open REST API connects without auth error."""
        device = BirdDogDevice(host="192.168.1.75", port=8080, password="birddog")

        mock_info = {
            "DeviceName": "BirdDog-Mini-01",
            "Model": "MINI",
            "Version": "v3.1.2",
            "EthernetMAC": "00:1A:2B:3C:4D:5E",
            "NetworkConfigMethod": "DHCP",
            "IPAddress": "192.168.1.75",
        }

        with patch.object(device, "check_auth_required", AsyncMock(return_value=False)), \
             patch.object(device, "get_device_info", AsyncMock(return_value=mock_info)):
            self.assertTrue(await device.test_connection())

    async def test_birddog_protected_device_auth_required_success(self):
        """Test device requiring auth succeeds when password is correct."""
        device = BirdDogDevice(host="192.168.1.50", port=8080, password="correct-password")
        with patch.object(device, "check_auth_required", AsyncMock(return_value=True)), \
             patch.object(device, "login", AsyncMock(return_value=True)), \
             patch.object(device, "get_device_info", AsyncMock(return_value={"DeviceName": "BirdDog-Play"})):
            self.assertTrue(await device.test_connection())

    async def test_birddog_protected_device_wrong_password_raises(self):
        """Test device requiring auth raises BirdDogAuthError on bad password."""
        device = BirdDogDevice(host="192.168.1.50", port=8080, password="wrong-password")
        with patch.object(device, "check_auth_required", AsyncMock(return_value=True)), \
             patch.object(device, "login", AsyncMock(return_value=False)):
            with self.assertRaises(BirdDogAuthError):
                await device.test_connection()

    async def test_birddog_operation_mode(self):
        """Test operation mode retrieval for Mini and Flex."""
        device = BirdDogDevice(host="192.168.1.75", port=8080)
        with patch.object(device, "_request", AsyncMock(return_value={"operationmode": "Encode"})):
            mode = await device.get_operation_mode()
            self.assertEqual(mode, "Encode")

    async def test_birddog_model_detection(self):
        """Test model recognition for MINI, FLEX, and PLAY."""
        device = BirdDogDevice(host="192.168.1.75", port=8080)

        with patch.object(device, "get_device_info", AsyncMock(return_value={"Model": "BirdDog Mini", "Version": "v3"})), \
             patch.object(device, "get_current_source", AsyncMock(return_value={"sourceName": "HDMI-Out"})), \
             patch.object(device, "get_operation_mode", AsyncMock(return_value="Decode")), \
             patch.object(device, "get_available_sources", AsyncMock(return_value=[])), \
             patch.object(device, "get_audio_mute", AsyncMock(return_value=False)):
            data = await device.fetch_all_data()
            self.assertEqual(data["model"], "MINI")
            self.assertEqual(data["operation_mode"], "Decode")

    async def test_birddog_current_source(self):
        """Test getting current NDI source."""
        device = BirdDogDevice(host="192.168.1.50", port=8080)
        mock_source = {"sourceName": "PROPRESENTER (Lyrics)"}

        with patch.object(device, "_request", AsyncMock(return_value=mock_source)):
            source_data = await device.get_current_source()
            self.assertEqual(source_data["sourceName"], "PROPRESENTER (Lyrics)")

    async def test_birddog_set_source(self):
        """Test setting NDI source via POST."""
        device = BirdDogDevice(host="192.168.1.50", port=8080)
        mock_request = AsyncMock(return_value={"status": "ok"})

        with patch.object(device, "_request", mock_request):
            result = await device.set_source("CAM-01 (Main)")
            self.assertTrue(result)
            mock_request.assert_called_once_with(
                "POST",
                "/connectTo",
                json_data={"sourceName": "CAM-01 (Main)"},
            )

    async def test_birddog_controls(self):
        """Test control endpoints: reboot, restart_video, refresh_sources."""
        device = BirdDogDevice(host="192.168.1.50", port=8080)
        mock_request = AsyncMock(return_value={"status": "ok"})

        with patch.object(device, "_request", mock_request):
            self.assertTrue(await device.reboot())
            mock_request.assert_called_with("POST", "/reboot")

            self.assertTrue(await device.restart_video())
            self.assertTrue(await device.refresh_sources())


if __name__ == "__main__":
    unittest.main()
