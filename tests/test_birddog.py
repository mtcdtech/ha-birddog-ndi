"""Tests for BirdDog Play, Mini, Flex API client using unittest.IsolatedAsyncioTestCase."""

import socket
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp

_real_getaddrinfo = socket.getaddrinfo

def _fast_getaddrinfo(host, port, *args, **kwargs):
    if str(host).endswith(".local"):
        return []
    try:
        return _real_getaddrinfo(host, port, *args, **kwargs)
    except Exception:
        return []

socket.getaddrinfo = _fast_getaddrinfo

# Mock homeassistant modules so tests run in lightweight environments
for mod in [
    "voluptuous",
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

class MockConfigFlow:
    """Mock base class for ConfigFlow."""
    def __init_subclass__(cls, **kwargs):
        pass
    def __init__(self):
        self.context = {}
        self.hass = MagicMock()
        self.unique_id = None
    def async_abort(self, *, reason):
        return {"type": "abort", "reason": reason}
    async def async_set_unique_id(self, unique_id):
        self.unique_id = unique_id
    def _abort_if_unique_id_configured(self, updates=None):
        pass
    def _async_current_entries(self):
        return []
    async def async_step_zeroconf_confirm(self, user_input=None):
        return {"type": "form", "step_id": "zeroconf_confirm"}
    def async_create_entry(self, *, title, data):
        return {"type": "create_entry", "title": title, "data": data}
    def async_show_form(self, **kwargs):
        return {"type": "form", **kwargs}

sys.modules["homeassistant.const"].CONF_HOST = "host"
sys.modules["homeassistant.const"].CONF_PORT = "port"
sys.modules["homeassistant.const"].CONF_NAME = "name"
sys.modules["homeassistant.const"].CONF_PASSWORD = "password"
sys.modules["homeassistant"].config_entries.ConfigFlow = MockConfigFlow
sys.modules["homeassistant.config_entries"].ConfigFlow = MockConfigFlow
from custom_components.birddog_ndi.config_flow import BirdDogConfigFlow

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


class TestBirdDogConfigFlow(unittest.IsolatedAsyncioTestCase):
    """Test suite for BirdDogConfigFlow de-duplication and discovery filtering."""

    def setUp(self):
        """Set up mocked config flow instance."""
        self.flow = BirdDogConfigFlow()
        self.flow.hass = MagicMock()

    async def test_zeroconf_aborts_when_already_configured_by_host(self):
        """Test zeroconf aborts immediately if host IP is already in configured entries."""
        existing_entry = MagicMock()
        existing_entry.data = {"host": "192.168.1.50"}
        existing_entry.unique_id = "192.168.1.50:8080"
        self.flow._async_current_entries = MagicMock(return_value=[existing_entry])

        discovery_info = MagicMock()
        discovery_info.name = "birddog-play-4a2b._http._tcp.local."
        discovery_info.hostname = "birddog-play.local."
        discovery_info.host = "192.168.1.50"
        discovery_info.port = 80

        result = await self.flow.async_step_zeroconf(discovery_info)
        self.assertEqual(result["type"], "abort")
        self.assertEqual(result["reason"], "already_configured")

    async def test_zeroconf_aborts_when_already_configured_by_legacy_unique_id(self):
        """Test zeroconf aborts if legacy unique_id (host:8080) matches."""
        existing_entry = MagicMock()
        existing_entry.data = {}
        existing_entry.unique_id = "192.168.1.75:8080"
        self.flow._async_current_entries = MagicMock(return_value=[existing_entry])

        discovery_info = MagicMock()
        discovery_info.name = "birddog-mini._http._tcp.local."
        discovery_info.hostname = "birddog-mini.local."
        discovery_info.host = "192.168.1.75"
        discovery_info.port = 80

        result = await self.flow.async_step_zeroconf(discovery_info)
        self.assertEqual(result["type"], "abort")
        self.assertEqual(result["reason"], "already_configured")

    async def test_zeroconf_aborts_when_not_birddog(self):
        """Test non-birddog mDNS services are ignored."""
        self.flow._async_current_entries = MagicMock(return_value=[])

        discovery_info = MagicMock()
        discovery_info.name = "apple-tv._http._tcp.local."
        discovery_info.hostname = "appletv.local."
        discovery_info.host = "192.168.1.99"
        discovery_info.port = 80

        result = await self.flow.async_step_zeroconf(discovery_info)
        self.assertEqual(result["type"], "abort")
        self.assertEqual(result["reason"], "not_birddog")

    async def test_user_step_aborts_when_already_configured(self):
        """Test manual step aborts if host is already configured."""
        existing_entry = MagicMock()
        existing_entry.data = {"host": "192.168.1.50"}
        existing_entry.unique_id = "192.168.1.50"
        self.flow._async_current_entries = MagicMock(return_value=[existing_entry])

        user_input = {
            "host": "192.168.1.50",
            "port": 8080,
            "password": "birddog",
            "name": "BirdDog Play",
        }

        result = await self.flow.async_step_user(user_input)
        self.assertEqual(result["type"], "abort")
        self.assertEqual(result["reason"], "already_configured")

    async def test_zeroconf_confirm_aborts_immediately_if_already_configured(self):
        """Test zeroconf_confirm aborts before displaying form if host was configured."""
        existing_entry = MagicMock()
        existing_entry.data = {"host": "192.168.1.50"}
        existing_entry.unique_id = "192.168.1.50"
        self.flow._async_current_entries = MagicMock(return_value=[existing_entry])

        self.flow._discovered_host = "192.168.1.50"
        result = await self.flow.async_step_zeroconf_confirm(user_input=None)
        self.assertEqual(result["type"], "abort")
        self.assertEqual(result["reason"], "already_configured")

    async def test_zeroconf_aborts_when_discovered_via_ipv6_with_ipv4_in_ip_addresses(self):
        """Test zeroconf aborts when mDNS arrives via IPv6 but IPv4 is in ip_addresses."""
        existing_entry = MagicMock()
        existing_entry.data = {"host": "192.168.1.50"}
        existing_entry.unique_id = "192.168.1.50"
        self.flow._async_current_entries = MagicMock(return_value=[existing_entry])

        discovery_info = MagicMock()
        discovery_info.name = "birddog-play-4a2b._http._tcp.local."
        discovery_info.hostname = "birddog-play.local."
        discovery_info.host = "fe80::20e:8eff:fe01:4a2b"
        discovery_info.ip_address = "fe80::20e:8eff:fe01:4a2b"
        discovery_info.ip_addresses = ["fe80::20e:8eff:fe01:4a2b", "192.168.1.50"]
        discovery_info.port = 80

        result = await self.flow.async_step_zeroconf(discovery_info)
        self.assertEqual(result["type"], "abort")
        self.assertEqual(result["reason"], "already_configured")

    async def test_zeroconf_aborts_when_hardware_name_suffix_matches_entry_title(self):
        """Test zeroconf aborts when hardware suffix (e.g. 94f8) matches entry title."""
        existing_entry = MagicMock()
        existing_entry.data = {"host": "10.0.0.12"}
        existing_entry.title = "BirdDog Play 94f8"
        existing_entry.unique_id = "bd_10.0.0.12"
        self.flow._async_current_entries = MagicMock(return_value=[existing_entry])

        discovery_info = MagicMock()
        discovery_info.name = "BirdDog-PLAY-94F8._http._tcp.local."
        discovery_info.hostname = "birddog-play-94f8.local."
        discovery_info.host = "fe80::ba13:3eff:fe3b:79d4"
        discovery_info.ip_address = "fe80::ba13:3eff:fe3b:79d4"
        discovery_info.ip_addresses = ["fe80::ba13:3eff:fe3b:79d4"]
        discovery_info.port = 80

        result = await self.flow.async_step_zeroconf(discovery_info)
        self.assertEqual(result["type"], "abort")
        self.assertEqual(result["reason"], "already_configured")

    async def test_zeroconf_aborts_when_matching_flow_already_in_progress(self):
        """Test zeroconf aborts with already_in_progress if another discovery flow is open."""
        self.flow._async_current_entries = MagicMock(return_value=[])
        self.flow._async_in_progress = MagicMock(
            return_value=[
                {
                    "flow_id": "other_flow_123",
                    "context": {
                        "source": "zeroconf",
                        "title_placeholders": {
                            "host": "192.168.1.60",
                            "name": "BirdDog-PLAY-1234",
                        },
                    },
                }
            ]
        )

        discovery_info = MagicMock()
        discovery_info.name = "BirdDog-PLAY-1234._birddog._tcp.local."
        discovery_info.hostname = "birddog-play-1234.local."
        discovery_info.host = "192.168.1.60"
        discovery_info.port = 80

        result = await self.flow.async_step_zeroconf(discovery_info)
        self.assertEqual(result["type"], "abort")
        self.assertEqual(result["reason"], "already_in_progress")

    async def test_zeroconf_allows_new_different_device(self):
        """Test zeroconf allows genuine new unconfigured device."""
        existing_entry = MagicMock()
        existing_entry.data = {"host": "192.168.1.50"}
        existing_entry.title = "BirdDog-PLAY-94F8"
        existing_entry.unique_id = "192.168.1.50"
        self.flow._async_current_entries = MagicMock(return_value=[existing_entry])
        self.flow._async_in_progress = MagicMock(return_value=[])

        discovery_info = MagicMock()
        discovery_info.name = "BirdDog-PLAY-5678._http._tcp.local."
        discovery_info.hostname = "birddog-play-5678.local."
        discovery_info.host = "192.168.1.51"
        discovery_info.port = 80

        result = await self.flow.async_step_zeroconf(discovery_info)
        self.assertEqual(result["type"], "form")
        self.assertEqual(result["step_id"], "zeroconf_confirm")


    async def test_auto_probe_port_8080_redirect(self):
        """Test BirdDogDevice initialized with port 80 auto-corrects to 8080 when REST API is on 8080."""
        device = BirdDogDevice(host="192.168.5.83", port=80, password="birddog")
        with patch.object(device, "_async_probe_port_8080", AsyncMock(side_effect=lambda: setattr(device, "port", 8080) or True)):
            with patch.object(device, "check_auth_required", AsyncMock(return_value=False)), \
                 patch.object(device, "get_device_info", AsyncMock(return_value={"MyHostName": "NDI-FellHall-Cam"})):
                self.assertTrue(await device.test_connection())
                self.assertEqual(device.port, 8080)

    async def test_birddog_mini_myhostname_and_dict_sources(self):
        """Test BirdDog Mini MyHostName resolution and dictionary-keyed sources parsing."""
        device = BirdDogDevice(host="192.168.5.83", port=8080)
        mock_info = {
            "manufacturer": "BirdDog",
            "DeviceType": "BirdDog",
            "Version": "1.0",
            "MyHostName": "NDI-FellHall-Cam",
        }
        mock_list = {
            "AVTEAMMACSTUDIO.LOCAL (Foyer)": "192.168.5.70:5962",
            "BIRDDOG-4951C (HDMI)": "192.168.5.83:5962",
        }

        with patch.object(device, "_request", AsyncMock(return_value=mock_list)):
            sources = await device.get_available_sources()
            self.assertIn("AVTEAMMACSTUDIO.LOCAL (Foyer)", sources)
            self.assertIn("BIRDDOG-4951C (HDMI)", sources)

        with patch.object(device, "get_device_info", AsyncMock(return_value=mock_info)), \
             patch.object(device, "get_current_source", AsyncMock(return_value={"sourceName": "RASSY (Test Pattern)"})), \
             patch.object(device, "get_operation_mode", AsyncMock(return_value=None)), \
             patch.object(device, "get_available_sources", AsyncMock(return_value=list(mock_list.keys()))), \
             patch.object(device, "get_audio_mute", AsyncMock(return_value=False)), \
             patch.object(device, "_request", AsyncMock(return_value={"ndiaudio": "unmute"})):
            data = await device.fetch_all_data()
            self.assertEqual(data["device_name"], "NDI-FellHall-Cam")
            self.assertEqual(data["model"], "MINI")
            self.assertEqual(data["current_source"], "RASSY (Test Pattern)")

    async def test_birddog_mini_mute_from_enc_settings(self):
        """Test audio mute status parsed from /enc-settings."""
        device = BirdDogDevice(host="192.168.5.83", port=8080)
        with patch.object(device, "_request", AsyncMock(return_value={"ndiaudio": "mute"})):
            muted = await device.get_audio_mute()
            self.assertTrue(muted)

    async def test_zeroconf_sets_discovered_port_to_8080(self):
        """Test Zeroconf _http._tcp on port 80 is normalized to DEFAULT_PORT (8080)."""
        self.flow._async_current_entries = MagicMock(return_value=[])
        self.flow._async_in_progress = MagicMock(return_value=[])

        discovery_info = MagicMock()
        discovery_info.name = "BirdDog-Mini-4951C._http._tcp.local."
        discovery_info.hostname = "birddog-mini-4951c.local."
        discovery_info.host = "192.168.5.83"
        discovery_info.port = 80

        result = await self.flow.async_step_zeroconf(discovery_info)
        self.assertEqual(result["type"], "form")
        self.assertEqual(result["step_id"], "zeroconf_confirm")
        self.assertEqual(self.flow._discovered_port, 8080)

    async def test_check_auth_required_raises_connection_error_when_unreachable(self):
        """Test check_auth_required raises BirdDogConnectionError when device is unreachable."""
        device = BirdDogDevice(host="192.0.2.1", port=8080, password="secret")
        mock_session = MagicMock()
        mock_session.get.side_effect = aiohttp.ClientConnectorError(
            connection_key=MagicMock(), os_error=OSError("Network unreachable")
        )
        with patch.object(device, "_get_session", AsyncMock(return_value=mock_session)):
            with self.assertRaises(BirdDogConnectionError):
                await device.check_auth_required()

    async def test_fetch_all_data_auto_probes_port_8080(self):
        """Test fetch_all_data automatically corrects port 80 to 8080."""
        device = BirdDogDevice(host="192.168.5.83", port=80, password="1400Frankford")
        with patch.object(device, "_async_probe_port_8080", AsyncMock(side_effect=lambda: setattr(device, "port", 8080) or True)), \
             patch.object(device, "get_device_info", AsyncMock(return_value={"DeviceName": "NDI-Cam", "Model": "MINI"})), \
             patch.object(device, "get_current_source", AsyncMock(return_value={"sourceName": "Cam 1"})), \
             patch.object(device, "get_operation_mode", AsyncMock(return_value=None)), \
             patch.object(device, "get_available_sources", AsyncMock(return_value=["Cam 1"])), \
             patch.object(device, "get_audio_mute", AsyncMock(return_value=False)):
            data = await device.fetch_all_data()
            self.assertEqual(device.port, 8080)
            self.assertEqual(data["device_name"], "NDI-Cam")


if __name__ == "__main__":
    unittest.main()


