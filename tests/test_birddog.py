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

    async def test_birddog_device_info_parsing(self):
        """Test parsing of device info endpoint."""
        device = BirdDogDevice(host="192.168.1.50", port=8080)

        mock_about_response = {
            "DeviceName": "Stage-Play-01",
            "Model": "PLAY",
            "Version": "v4.5.1",
            "Serial": "BDPLAY12345",
            "MacAddress": "00:1A:2B:3C:4D:5E",
        }

        with patch.object(device, "_request", AsyncMock(return_value=mock_about_response)):
            info = await device.get_device_info()
            self.assertEqual(info["DeviceName"], "Stage-Play-01")
            self.assertEqual(info["Model"], "PLAY")
            self.assertEqual(info["Version"], "v4.5.1")
            self.assertEqual(info["MacAddress"], "00:1A:2B:3C:4D:5E")

    async def test_birddog_current_source(self):
        """Test getting current NDI source with location=decoder format."""
        device = BirdDogDevice(host="192.168.1.50", port=8080)

        mock_source = {
            "sourceHostname": "PROPRESENTER",
            "sourceStreamName": "Lyrics",
            "sourceIP": "192.168.1.100",
            "sourcePort": 5961,
        }

        with patch.object(device, "_request", AsyncMock(return_value=mock_source)):
            source_data = await device.get_current_source()
            self.assertEqual(source_data["sourceHostname"], "PROPRESENTER")
            self.assertEqual(source_data["sourceStreamName"], "Lyrics")
            self.assertEqual(source_data["sourceIP"], "192.168.1.100")

    async def test_birddog_set_source(self):
        """Test setting NDI source via POST."""
        device = BirdDogDevice(host="192.168.1.50", port=8080)

        mock_request = AsyncMock(return_value={"status": "ok"})
        with patch.object(device, "_request", mock_request):
            result = await device.set_source("CAM-01 (Main)")
            self.assertTrue(result)

    async def test_birddog_controls(self):
        """Test auxiliary control endpoints: reboot, transport, screensaver, tally."""
        device = BirdDogDevice(host="192.168.1.50", port=8080)

        mock_request = AsyncMock(return_value={"status": "ok"})
        with patch.object(device, "_request", mock_request):
            # Reboot
            self.assertTrue(await device.reboot())
            mock_request.assert_called_with("POST", "/reboot")

            # Restart video
            self.assertTrue(await device.restart_video())

            # Set screensaver
            self.assertTrue(await device.set_screensaver("Black"))

            # Set transport
            self.assertTrue(await device.set_transport("UDP"))

            # Set tally
            self.assertTrue(await device.set_tally(True))

    async def test_birddog_fetch_all_data(self):
        """Test fetching all data aggregate with rich decoder status."""
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
                "MacAddress": "00:11:22:33:44:55",
            }),
        ), patch.object(
            device,
            "get_current_source",
            AsyncMock(return_value={
                "sourceHostname": "SWITCHER",
                "sourceStreamName": "Program",
                "sourceIP": "192.168.1.10",
                "sourcePort": 5960,
            }),
        ), patch.object(
            device,
            "get_failover_source",
            AsyncMock(return_value={"sourceName": "BACKUP (Stream)"}),
        ), patch.object(
            device,
            "get_decode_status",
            AsyncMock(return_value={"bitrate": "120 Mbps", "resolution": "1080p60"}),
        ), patch.object(
            device,
            "get_decode_setup",
            AsyncMock(return_value={"TallyMode": "On", "ScreenSaverMode": "Logo"}),
        ), patch.object(
            device,
            "get_decode_transport",
            AsyncMock(return_value="TCP"),
        ), patch.object(
            device,
            "get_video_output",
            AsyncMock(return_value={"format": "1080p60"}),
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
            self.assertEqual(data["source_ip"], "192.168.1.10")
            self.assertEqual(data["source_port"], 5960)
            self.assertEqual(data["failover_source"], "BACKUP (Stream)")
            self.assertEqual(data["bitrate"], "120 Mbps")
            self.assertEqual(data["transport"], "TCP")
            self.assertEqual(data["screensaver"], "Logo")
            self.assertTrue(data["tally_on"])
            self.assertTrue(data["is_decoding"])
            self.assertEqual(data["mac_address"], "00:11:22:33:44:55")


if __name__ == "__main__":
    unittest.main()
