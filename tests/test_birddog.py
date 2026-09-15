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

    async def test_birddog_login_success(self):
        """Test successful authentication."""
        device = BirdDogDevice(host="192.168.1.50", port=8080, password="correct-password")
        with patch.object(device, "login", AsyncMock(return_value=True)):
            self.assertTrue(await device.login())

    async def test_birddog_login_invalid_password_raises(self):
        """Test that wrong password is detected before adding device."""
        device = BirdDogDevice(host="192.168.1.50", port=8080, password="wrong-password")
        with patch.object(device, "login", AsyncMock(return_value=False)):
            with self.assertRaises(BirdDogAuthError):
                await device.test_connection()

    async def test_birddog_device_info_parsing(self):
        """Test parsing of device info endpoint."""
        device = BirdDogDevice(host="192.168.1.50", port=8080)

        mock_about_response = {
            "DeviceName": "Stage-Play-01",
            "Model": "PLAY",
            "Version": "v4.5.1",
            "Serial": "BDPLAY12345",
            "EthernetMAC": "00:1A:2B:3C:4D:5E",
            "NetworkConfigMethod": "DHCP",
            "IPAddress": "192.168.1.50",
            "Netmask": "255.255.255.0",
            "GateWay": "192.168.1.1",
        }

        with patch.object(device, "_request", AsyncMock(return_value=mock_about_response)):
            info = await device.get_device_info()
            self.assertEqual(info["DeviceName"], "Stage-Play-01")
            self.assertEqual(info["Model"], "PLAY")
            self.assertEqual(info["Version"], "v4.5.1")
            self.assertEqual(info["EthernetMAC"], "00:1A:2B:3C:4D:5E")

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

    async def test_birddog_fetch_all_data(self):
        """Test fetching all data aggregate with clean PLAY telemetry."""
        device = BirdDogDevice(host="192.168.1.50", port=8080)

        with patch.object(
            device,
            "login",
            AsyncMock(return_value=True),
        ), patch.object(
            device,
            "get_device_info",
            AsyncMock(return_value={
                "DeviceName": "Auditorium-Play",
                "Model": "PLAY",
                "Version": "v5.0",
                "EthernetMAC": "00:11:22:33:44:55",
                "NetworkConfigMethod": "DHCP",
                "IPAddress": "192.168.1.50",
                "Netmask": "255.255.255.0",
                "GateWay": "192.168.1.1",
            }),
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
            self.assertEqual(data["mac_address"], "00:11:22:33:44:55")
            self.assertEqual(data["network_mode"], "DHCP")
            self.assertEqual(data["ip_address"], "192.168.1.50")
            self.assertTrue(data["is_decoding"])
            self.assertFalse(data["audio_muted"])


if __name__ == "__main__":
    unittest.main()
