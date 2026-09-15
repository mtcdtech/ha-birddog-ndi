"""Asynchronous client for interacting with BirdDog PLAY NDI devices."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import aiohttp

from .const import (
    DEFAULT_PASSWORD,
    DEFAULT_PORT,
    ENDPOINT_ABOUT,
    ENDPOINT_ANALOG_SETUP,
    ENDPOINT_AUDIO_GAIN,
    ENDPOINT_CONNECT_TO,
    ENDPOINT_DECODE_SETUP,
    ENDPOINT_DECODE_STATUS,
    ENDPOINT_DECODE_TRANSPORT,
    ENDPOINT_LIST,
    ENDPOINT_LOGIN,
    ENDPOINT_REBOOT,
    ENDPOINT_REFRESH,
    ENDPOINT_RESTART_VIDEO,
    ENDPOINT_VERSION,
    ENDPOINT_VIDEO_OUTPUT,
)

_LOGGER = logging.getLogger(__name__)


class BirdDogAPIError(Exception):
    """General BirdDog API exception."""


class BirdDogConnectionError(BirdDogAPIError):
    """Exception when unable to connect to BirdDog device."""


class BirdDogAuthError(BirdDogAPIError):
    """Exception when authentication fails."""


class BirdDogDevice:
    """Client representation of a BirdDog PLAY NDI device."""

    def __init__(
        self,
        host: str,
        port: int = DEFAULT_PORT,
        password: str = DEFAULT_PASSWORD,
        session: aiohttp.ClientSession | None = None,
        timeout: int = 5,
    ) -> None:
        """Initialize the BirdDog device client."""
        self.host = host
        self.port = port
        self.password = password
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session = session
        self._own_session = False
        self._authenticated = False

    @property
    def base_url(self) -> str:
        """Return the base URL of the BirdDog device."""
        return f"http://{self.host}:{self.port}"

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp client session with cookie jar."""
        if self._session is None or self._session.closed:
            jar = aiohttp.CookieJar(unsafe=True)
            self._session = aiohttp.ClientSession(
                cookie_jar=jar,
                timeout=self.timeout,
            )
            self._own_session = True
        return self._session

    async def close(self) -> None:
        """Close the session if created internally."""
        if self._own_session and self._session and not self._session.closed:
            await self._session.close()

    async def login(self) -> bool:
        """Authenticate with the BirdDog device via /login."""
        if not self.password:
            self._authenticated = True
            return True

        session = await self._get_session()
        payloads = [
            {"auth_password": self.password},
            {"password": self.password},
        ]

        # Try configured port first, fallback to port 80 if configured port is 8080
        ports_to_try = [self.port]
        if self.port != 80:
            ports_to_try.append(80)

        for port in ports_to_try:
            url = f"http://{self.host}:{port}{ENDPOINT_LOGIN}"
            for payload in payloads:
                try:
                    # Send as form-urlencoded (standard BirdUI login form)
                    async with session.post(url, data=payload, allow_redirects=True) as resp:
                        if resp.status in (200, 204, 302):
                            text = await resp.text()
                            if "incorrect" not in text.lower() and "invalid password" not in text.lower():
                                _LOGGER.debug("Successfully authenticated with BirdDog on %s:%s", self.host, port)
                                self._authenticated = True
                                return True

                    # Also try JSON format
                    async with session.post(url, json=payload, allow_redirects=True) as resp:
                        if resp.status in (200, 204, 302):
                            self._authenticated = True
                            return True
                except (aiohttp.ClientError, asyncio.TimeoutError) as err:
                    _LOGGER.debug("Login attempt to %s failed: %s", url, err)

        self._authenticated = False
        return False

    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        retry_auth: bool = True,
    ) -> Any:
        """Execute an async HTTP request with auto-relogin handling."""
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}"

        headers = {
            "Accept": "application/json, text/plain, */*",
        }

        try:
            async with session.request(
                method,
                url,
                json=json_data,
                params=params,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=True,
            ) as response:
                # If redirected to /login or returned 401/403, authenticate and retry once
                if response.status in (401, 403) or (
                    response.history and any("/login" in str(r.url) for r in response.history)
                ):
                    if retry_auth:
                        _LOGGER.debug("Authentication required for %s, logging in...", endpoint)
                        await self.login()
                        return await self._request(
                            method,
                            endpoint,
                            json_data=json_data,
                            params=params,
                            retry_auth=False,
                        )
                    raise BirdDogAuthError(f"Unauthorized access to {endpoint}")

                if response.status >= 400:
                    text = await response.text()
                    raise BirdDogAPIError(
                        f"HTTP {response.status} from {endpoint}: {text}"
                    )

                content_type = response.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    return await response.json()
                text = await response.text()
                # Check if text is login HTML
                if "<form" in text and ("auth_password" in text or "login" in text):
                    if retry_auth:
                        _LOGGER.debug("Received login form for %s, authenticating...", endpoint)
                        await self.login()
                        return await self._request(
                            method,
                            endpoint,
                            json_data=json_data,
                            params=params,
                            retry_auth=False,
                        )
                try:
                    return json.loads(text)
                except Exception:
                    return text.strip()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise BirdDogConnectionError(
                f"Failed to connect to BirdDog device at {self.host}:{self.port}: {err}"
            ) from err

    async def test_connection(self) -> bool:
        """Test if the device is reachable and authenticates."""
        try:
            if self.password:
                await self.login()

            # Try /about or /connectTo
            info = await self.get_device_info()
            if info:
                return True
            source = await self.get_current_source()
            return bool(source)
        except Exception as err:
            _LOGGER.debug("Connection test failed: %s", err)
            return False

    async def get_device_info(self) -> dict[str, Any]:
        """Fetch general device information from /about or /version."""
        for ep in (ENDPOINT_ABOUT, ENDPOINT_VERSION):
            try:
                data = await self._request("GET", ep)
                if isinstance(data, dict):
                    return data
                if isinstance(data, str) and data:
                    return {"Version": data}
            except BirdDogAPIError as err:
                _LOGGER.debug("Endpoint %s failed: %s", ep, err)
        return {}

    async def get_current_source(self) -> dict[str, Any]:
        """Fetch current connected NDI source from /connectTo?location=decoder or /connectTo."""
        for ep, params in [
            (ENDPOINT_CONNECT_TO, {"location": "decoder"}),
            (ENDPOINT_CONNECT_TO, None),
        ]:
            try:
                data = await self._request("GET", ep, params=params)
                if isinstance(data, dict) and data:
                    return data
                if isinstance(data, str) and data and not data.startswith("<"):
                    return {"sourceName": data}
            except BirdDogAPIError as err:
                _LOGGER.debug("GET %s (params=%s) failed: %s", ep, params, err)
        return {}

    async def get_failover_source(self) -> dict[str, Any]:
        """Fetch failover source if configured."""
        try:
            data = await self._request("GET", ENDPOINT_CONNECT_TO, params={"location": "DecoderFailOver"})
            if isinstance(data, dict):
                return data
        except BirdDogAPIError:
            pass
        return {}

    async def get_decode_status(self) -> dict[str, Any]:
        """Fetch decoder real-time status (bitrate, resolution, operational health)."""
        try:
            data = await self._request("GET", ENDPOINT_DECODE_STATUS)
            if isinstance(data, dict):
                return data
        except BirdDogAPIError:
            pass
        return {}

    async def get_decode_setup(self) -> dict[str, Any]:
        """Fetch decoder configuration (ColorSpace, TallyMode, ScreenSaverMode, NDIAudio)."""
        try:
            data = await self._request("GET", ENDPOINT_DECODE_SETUP)
            if isinstance(data, dict):
                return data
        except BirdDogAPIError:
            pass
        return {}

    async def get_decode_transport(self) -> str:
        """Fetch active decode transport protocol (TCP, UDP, Multicast)."""
        try:
            data = await self._request("GET", ENDPOINT_DECODE_TRANSPORT)
            if isinstance(data, dict):
                return data.get("transport") or data.get("Transport") or "TCP"
            if isinstance(data, str) and data and not data.startswith("<"):
                return data
        except BirdDogAPIError:
            pass
        return "TCP"

    async def get_video_output(self) -> dict[str, Any]:
        """Fetch video output format/resolution."""
        for ep in (ENDPOINT_VIDEO_OUTPUT, "/videooutputformat"):
            try:
                data = await self._request("GET", ep)
                if isinstance(data, dict):
                    return data
                if isinstance(data, str) and data and not data.startswith("<"):
                    return {"format": data}
            except BirdDogAPIError:
                pass
        return {}

    async def get_available_sources(self) -> list[str]:
        """Fetch list of discovered NDI sources if supported."""
        for endpoint in (ENDPOINT_LIST, ENDPOINT_REFRESH):
            try:
                data = await self._request("GET", endpoint)
                if isinstance(data, list):
                    return [str(s) for s in data if s]
                if isinstance(data, dict):
                    sources = data.get("sources") or data.get("sourceList") or data.get("discoveredSources") or []
                    if isinstance(sources, list):
                        return [str(s) for s in sources if s]
            except BirdDogAPIError:
                continue
        return []

    async def set_source(self, source_name: str) -> bool:
        """Switch NDI decode stream to source_name via POST /connectTo."""
        _LOGGER.info("Switching BirdDog %s NDI source to: %s", self.host, source_name)
        parts = source_name.split(" ", 1)
        hostname = parts[0].strip("()")
        stream_name = parts[1].strip("()") if len(parts) > 1 else source_name

        payloads = [
            {"sourceHostname": hostname, "sourceStreamName": stream_name, "sourceName": source_name},
            {"sourceName": source_name},
        ]

        for payload in payloads:
            for params in [{"location": "decoder"}, None]:
                try:
                    await self._request("POST", ENDPOINT_CONNECT_TO, json_data=payload, params=params)
                    return True
                except BirdDogAPIError as err:
                    _LOGGER.debug("POST %s (params=%s) failed: %s", ENDPOINT_CONNECT_TO, params, err)
        return False

    async def set_failover_source(self, source_name: str) -> bool:
        """Set failover NDI source via POST /connectTo?location=DecoderFailOver."""
        parts = source_name.split(" ", 1)
        hostname = parts[0].strip("()")
        stream_name = parts[1].strip("()") if len(parts) > 1 else source_name
        payload = {"sourceHostname": hostname, "sourceStreamName": stream_name, "sourceName": source_name}
        try:
            await self._request("POST", ENDPOINT_CONNECT_TO, json_data=payload, params={"location": "DecoderFailOver"})
            return True
        except BirdDogAPIError as err:
            _LOGGER.error("Failed to set failover NDI source: %s", err)
            return False

    async def get_audio_mute(self) -> bool:
        """Fetch audio mute status."""
        for ep in (ENDPOINT_AUDIO_GAIN, ENDPOINT_ANALOG_SETUP):
            try:
                data = await self._request("GET", ep)
                if isinstance(data, dict):
                    return bool(data.get("mute") or data.get("Mute") or data.get("muted"))
            except BirdDogAPIError:
                pass
        return False

    async def set_audio_mute(self, mute: bool) -> bool:
        """Set audio mute state."""
        for ep in (ENDPOINT_AUDIO_GAIN, ENDPOINT_ANALOG_SETUP):
            try:
                await self._request("POST", ep, json_data={"mute": mute})
                return True
            except BirdDogAPIError:
                pass
        return False

    async def set_tally(self, enabled: bool) -> bool:
        """Set Tally light state."""
        try:
            mode = "On" if enabled else "Off"
            await self._request("POST", ENDPOINT_DECODE_SETUP, json_data={"TallyMode": mode})
            return True
        except BirdDogAPIError as err:
            _LOGGER.debug("Setting tally failed: %s", err)
            return False

    async def set_screensaver(self, mode: str) -> bool:
        """Set screen saver mode (e.g. Logo, Black, ScreenSaver)."""
        try:
            await self._request("POST", ENDPOINT_DECODE_SETUP, json_data={"ScreenSaverMode": mode})
            return True
        except BirdDogAPIError as err:
            _LOGGER.debug("Setting screensaver failed: %s", err)
            return False

    async def set_transport(self, transport: str) -> bool:
        """Set decode transport protocol (TCP, UDP, Multicast)."""
        try:
            await self._request("POST", ENDPOINT_DECODE_TRANSPORT, json_data={"transport": transport})
            return True
        except BirdDogAPIError as err:
            _LOGGER.debug("Setting transport failed: %s", err)
            return False

    async def reboot(self) -> bool:
        """Reboot the BirdDog PLAY device."""
        _LOGGER.warning("Rebooting BirdDog device at %s", self.host)
        try:
            await self._request("POST", ENDPOINT_REBOOT)
            return True
        except BirdDogAPIError as err:
            _LOGGER.error("Failed to reboot device: %s", err)
            return False

    async def restart_video(self) -> bool:
        """Restart video decoding subsystem."""
        _LOGGER.info("Restarting video engine on BirdDog %s", self.host)
        for ep in (ENDPOINT_RESTART_VIDEO, "/restart"):
            try:
                await self._request("POST", ep)
                return True
            except BirdDogAPIError:
                pass
        return False

    async def refresh_sources(self) -> bool:
        """Trigger NDI source refresh scan on device."""
        try:
            await self._request("POST", ENDPOINT_REFRESH)
            return True
        except BirdDogAPIError:
            return False

    async def fetch_all_data(self) -> dict[str, Any]:
        """Fetch all device states in a single polling cycle."""
        # Ensure authenticated
        if not self._authenticated and self.password:
            await self.login()

        info = await self.get_device_info()
        source_data = await self.get_current_source()
        failover_data = await self.get_failover_source()
        decode_status = await self.get_decode_status()
        decode_setup = await self.get_decode_setup()
        transport = await self.get_decode_transport()
        video_out = await self.get_video_output()
        mute_state = await self.get_audio_mute()

        # Parse current source
        current_source = (
            source_data.get("sourceName")
            or (
                f"{source_data.get('sourceHostname', '')} ({source_data.get('sourceStreamName', '')})"
                if source_data.get("sourceHostname") and source_data.get("sourceStreamName")
                else None
            )
            or source_data.get("sourceStreamName")
            or "Unknown"
        )

        failover_source = (
            failover_data.get("sourceName")
            or (
                f"{failover_data.get('sourceHostname', '')} ({failover_data.get('sourceStreamName', '')})"
                if failover_data.get("sourceHostname") and failover_data.get("sourceStreamName")
                else None
            )
            or "None"
        )

        # Discovered sources
        sources = await self.get_available_sources()
        for s in (current_source, failover_source):
            if s and s not in ("Unknown", "None") and s not in sources:
                sources.insert(0, s)

        # Video format resolution
        video_format = (
            video_out.get("format")
            or video_out.get("VideoFormat")
            or decode_status.get("resolution")
            or decode_status.get("Format")
            or "Auto"
        )

        # Bitrate
        bitrate = decode_status.get("bitrate") or decode_status.get("BitRate") or "0 Mbps"

        # Tally state
        tally_mode = decode_setup.get("TallyMode") or decode_setup.get("tally") or "Off"
        tally_on = str(tally_mode).lower() in ("on", "true", "1")

        # Screensaver mode
        screensaver = decode_setup.get("ScreenSaverMode") or decode_setup.get("screensaver") or "Logo"

        # Decoding active binary state
        is_decoding = current_source not in ("Unknown", "None", "")

        return {
            "online": True,
            "host": self.host,
            "port": self.port,
            "device_name": info.get("DeviceName") or info.get("name") or "BirdDog Play",
            "model": info.get("Model") or info.get("model") or "PLAY",
            "firmware": info.get("Version") or info.get("firmware") or info.get("version") or "Unknown",
            "serial": info.get("Serial") or info.get("serialNumber") or f"bd_{self.host}",
            "mac_address": info.get("MacAddress") or info.get("MAC") or info.get("mac") or "Unknown",
            "current_source": current_source,
            "source_ip": source_data.get("sourceIP") or "Unknown",
            "source_port": source_data.get("sourcePort") or "Unknown",
            "failover_source": failover_source,
            "available_sources": sources,
            "video_format": str(video_format),
            "bitrate": str(bitrate),
            "transport": str(transport),
            "screensaver": str(screensaver),
            "tally_on": tally_on,
            "audio_muted": mute_state,
            "is_decoding": is_decoding,
        }
