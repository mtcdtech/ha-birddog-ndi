"""Asynchronous client for interacting with BirdDog NDI devices (Play, Play Pro, Mini, Flex, Studio)."""

from __future__ import annotations

import asyncio
import base64
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
    ENDPOINT_LIST,
    ENDPOINT_LOGIN,
    ENDPOINT_OPERATION_MODE,
    ENDPOINT_REBOOT,
    ENDPOINT_REFRESH,
    ENDPOINT_RESTART_VIDEO,
    ENDPOINT_VERSION,
)

_LOGGER = logging.getLogger(__name__)


class BirdDogAPIError(Exception):
    """General BirdDog API exception."""


class BirdDogConnectionError(BirdDogAPIError):
    """Exception when unable to connect to BirdDog device."""


class BirdDogAuthError(BirdDogAPIError):
    """Exception when authentication fails."""


class BirdDogDevice:
    """Client representation of a BirdDog NDI device (Play, Mini, Flex, etc.)."""

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
        self._auth_required: bool | None = None
        self._authenticated = False
        self._session_token: str | None = None

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

    async def _async_probe_port_8080(self) -> bool:
        """Check if port 8080 hosts an active BirdDog REST API when port 80 was configured."""
        if self.port != 80:
            return False
        session = await self._get_session()
        probe_url = f"http://{self.host}:{DEFAULT_PORT}{ENDPOINT_ABOUT}"
        try:
            async with session.get(probe_url, timeout=self.timeout) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    try:
                        data = json.loads(text)
                        if isinstance(data, dict):
                            _LOGGER.info(
                                "BirdDog device at %s has active REST API on port %s; auto-correcting from port 80",
                                self.host,
                                DEFAULT_PORT,
                            )
                            self.port = DEFAULT_PORT
                            return True
                    except Exception:
                        pass
        except (aiohttp.ClientError, asyncio.TimeoutError):
            pass
        return False

    async def check_auth_required(self) -> bool:
        """Determine adaptively if the device REST API requires authentication."""
        # Auto-correct port 80 to 8080 if REST API is responsive on 8080
        if self.port == 80:
            await self._async_probe_port_8080()

        session = await self._get_session()
        probe_endpoints = [ENDPOINT_ABOUT, ENDPOINT_VERSION, ENDPOINT_OPERATION_MODE, ENDPOINT_CONNECT_TO]

        for ep in probe_endpoints:
            url = f"{self.base_url}{ep}"
            try:
                async with session.get(url, timeout=self.timeout, allow_redirects=True) as resp:
                    if resp.status in (401, 403) or (
                        resp.history and any("/login" in str(r.url) for r in resp.history)
                    ):
                        self._auth_required = True
                        return True

                    text = await resp.text()
                    # Check if returned login HTML form
                    lower_text = text.lower()
                    if "<form" in lower_text and ("auth_password" in lower_text or 'type="password"' in lower_text):
                        # If on port 80, the web portal is protected but port 8080 REST API might be open
                        if self.port == 80 and await self._async_probe_port_8080():
                            return await self.check_auth_required()
                        self._auth_required = True
                        return True

                    # If valid JSON or non-empty non-HTML text returned, API is open (Mini / Flex)
                    if resp.status == 200:
                        try:
                            json.loads(text)
                            self._auth_required = False
                            self._authenticated = True
                            _LOGGER.debug("BirdDog at %s has open REST API (auth not required)", self.host)
                            return False
                        except Exception:
                            if not lower_text.startswith("<!doctype") and not lower_text.startswith("<html"):
                                self._auth_required = False
                                self._authenticated = True
                                return False
            except (aiohttp.ClientError, asyncio.TimeoutError):
                continue

        # Default to requiring auth if cannot conclusively determine
        self._auth_required = bool(self.password)
        return self._auth_required

    async def login(self) -> bool:
        """Authenticate with the BirdDog device via /login on port 80 or 8080."""
        if not self.password:
            self._authenticated = True
            return True

        session = await self._get_session()
        payload = {"auth_password": self.password}

        # Try port 80 (BirdUI standard web port), then the configured port
        ports_to_try = [80]
        if self.port not in ports_to_try:
            ports_to_try.append(self.port)

        for port in ports_to_try:
            url = f"http://{self.host}:{port}{ENDPOINT_LOGIN}"
            try:
                # Intercept redirects with allow_redirects=False to capture cookies before aiohttp clearance collision
                async with session.post(
                    url,
                    data=payload,
                    timeout=self.timeout,
                    allow_redirects=False,
                ) as resp:
                    raw_cookies = resp.headers.getall("Set-Cookie", [])
                    for c in raw_cookies:
                        if "BirdDogSession=" in c and "Max-Age=0" not in c:
                            val = c.split("BirdDogSession=")[1].split(";")[0].strip()
                            if val:
                                self._session_token = val
                                try:
                                    from yarl import URL
                                    session.cookie_jar.update_cookies({"BirdDogSession": val}, URL(f"http://{self.host}:{port}"))
                                except Exception:
                                    pass
                                break

                    location = resp.headers.get("Location", "")
                    if resp.status in (302, 303) and location and location != ENDPOINT_LOGIN:
                        self._authenticated = True
                        _LOGGER.debug("Successfully authenticated with BirdDog on %s:%s (redirected to %s)", self.host, port, location)
                        return True

                    if resp.status in (401, 403):
                        _LOGGER.warning("BirdDog at %s:%s rejected password (HTTP %s)", self.host, port, resp.status)
                        continue

                    text = await resp.text()
                    lower_text = text.lower()

                    # Check for explicit failure markers
                    if (
                        "invalid password" in lower_text
                        or "incorrect password" in lower_text
                        or "unauthorized" in lower_text
                        or "login failed" in lower_text
                    ):
                        _LOGGER.warning("BirdDog at %s:%s reported invalid password", self.host, port)
                        continue

                    # If the response no longer renders the login form, login was successful
                    if "auth_form" not in lower_text and "auth_password" not in lower_text:
                        self._authenticated = True
                        _LOGGER.debug("Successfully authenticated with BirdDog on %s:%s", self.host, port)
                        return True

                    _LOGGER.warning("BirdDog at %s:%s re-rendered login form", self.host, port)
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
        """Execute an async HTTP request with adaptive authentication handling."""
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}"

        headers = {
            "Accept": "application/json, text/plain, */*",
        }

        if self._session_token:
            headers["Cookie"] = f"BirdDogSession={self._session_token}"

        # If HTTP Basic Auth header needed
        if self.password and self._auth_required:
            auth_str = f"admin:{self.password}"
            b64_auth = base64.b64encode(auth_str.encode()).decode()
            headers["Authorization"] = f"Basic {b64_auth}"

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
                    self._auth_required = True
                    if retry_auth and self.password:
                        _LOGGER.debug("Authentication required for %s, logging in...", endpoint)
                        auth_ok = await self.login()
                        if not auth_ok:
                            raise BirdDogAuthError("Invalid credentials for BirdDog device")
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
                if "<form" in text and ("auth_password" in text or "login" in text):
                    self._auth_required = True
                    if retry_auth and self.password:
                        auth_ok = await self.login()
                        if not auth_ok:
                            raise BirdDogAuthError("Invalid credentials for BirdDog device")
                        return await self._request(
                            method,
                            endpoint,
                            json_data=json_data,
                            params=params,
                            retry_auth=False,
                        )
                    raise BirdDogAuthError(f"Unauthorized access to {endpoint}")

                try:
                    return json.loads(text)
                except Exception:
                    return text.strip()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise BirdDogConnectionError(
                f"Failed to connect to BirdDog device at {self.host}:{self.port}: {err}"
            ) from err

    async def test_connection(self) -> bool:
        """Adaptively test if device is reachable and valid before adding."""
        # 0. Check and auto-correct port 80 to 8080 if REST API is on 8080
        if self.port == 80:
            await self._async_probe_port_8080()

        # 1. Adaptively check if authentication is needed
        auth_needed = await self.check_auth_required()

        # 2. If authentication is strictly required, validate the password
        if auth_needed and self.password:
            auth_ok = await self.login()
            if not auth_ok:
                raise BirdDogAuthError("Invalid password for BirdDog device")

        # 3. Test retrieving device telemetry
        try:
            info = await self.get_device_info()
            if info:
                return True
            source = await self.get_current_source()
            if source:
                return True
            op_mode = await self.get_operation_mode()
            if op_mode:
                return True
            # Fallback probe
            session = await self._get_session()
            async with session.get(self.base_url, timeout=self.timeout) as resp:
                if resp.status < 500:
                    return True
        except BirdDogAuthError:
            raise
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise BirdDogConnectionError(f"Cannot reach BirdDog at {self.host}:{self.port}: {err}") from err

        raise BirdDogConnectionError(f"BirdDog device at {self.host}:{self.port} not responding")

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
        """Fetch current connected NDI source from /connectTo."""
        try:
            data = await self._request("GET", ENDPOINT_CONNECT_TO)
            if isinstance(data, dict) and data:
                return data
            if isinstance(data, str) and data and not data.startswith("<"):
                return {"sourceName": data}
        except BirdDogAPIError as err:
            _LOGGER.debug("GET %s failed: %s", ENDPOINT_CONNECT_TO, err)
        return {}

    async def get_operation_mode(self) -> str | None:
        """Fetch operation mode (Decode vs Encode) for converters like Mini and Flex."""
        try:
            data = await self._request("GET", ENDPOINT_OPERATION_MODE)
            if isinstance(data, dict):
                return data.get("operationmode") or data.get("mode") or data.get("OperationMode")
            if isinstance(data, str) and data and not data.startswith("<"):
                return data
        except BirdDogAPIError as err:
            _LOGGER.debug("GET %s failed: %s", ENDPOINT_OPERATION_MODE, err)
        return None

    async def get_available_sources(self) -> list[str]:
        """Fetch list of discovered NDI sources if supported."""
        for endpoint in (ENDPOINT_LIST, ENDPOINT_REFRESH):
            try:
                data = await self._request("GET", endpoint)
                if isinstance(data, list):
                    return [str(s) for s in data if s]
                if isinstance(data, dict):
                    sources = (
                        data.get("sources")
                        or data.get("sourceList")
                        or data.get("discoveredSources")
                    )
                    if isinstance(sources, list):
                        return [str(s) for s in sources if s]
                    # On BirdDog Mini, /list returns a dict mapping stream names to IP:port
                    # e.g. {"AVTEAMMACSTUDIO.LOCAL (Foyer)": "192.168.5.70:5962", ...}
                    dict_sources = [str(k) for k in data.keys() if k and not str(k).startswith("_")]
                    if dict_sources:
                        return dict_sources
            except BirdDogAPIError:
                continue
        return []

    async def set_source(self, source_name: str) -> bool:
        """Switch NDI decode stream to source_name via POST /connectTo."""
        _LOGGER.info("Switching BirdDog %s NDI source to: %s", self.host, source_name)
        payload = {"sourceName": source_name}
        try:
            await self._request("POST", ENDPOINT_CONNECT_TO, json_data=payload)
            return True
        except BirdDogAPIError as err:
            _LOGGER.error("Failed to set NDI source to %s: %s", source_name, err)
            raise

    async def get_audio_mute(self) -> bool:
        """Fetch audio mute status."""
        for ep in (ENDPOINT_AUDIO_GAIN, ENDPOINT_ANALOG_SETUP, "/enc-settings"):
            try:
                data = await self._request("GET", ep)
                if isinstance(data, dict):
                    if "ndiaudio" in data:
                        return str(data.get("ndiaudio")).lower() == "mute"
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

    async def reboot(self) -> bool:
        """Reboot the BirdDog device."""
        _LOGGER.warning("Rebooting BirdDog device at %s", self.host)
        try:
            await self._request("POST", ENDPOINT_REBOOT)
            return True
        except BirdDogAPIError as err:
            _LOGGER.error("Failed to reboot device: %s", err)
            return False

    async def restart_video(self) -> bool:
        """Restart video decoding/encoding subsystem."""
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
        if self._auth_required and not self._authenticated and self.password:
            await self.login()

        info = await self.get_device_info()
        source_data = await self.get_current_source()
        op_mode = await self.get_operation_mode()
        mute_state = await self.get_audio_mute()

        # Resilient source resolution
        current_source = (
            source_data.get("sourceName")
            or source_data.get("source")
            or (
                f"{source_data.get('sourceHostname', '')} ({source_data.get('sourceStreamName', '')})"
                if source_data.get("sourceHostname") and source_data.get("sourceStreamName")
                else None
            )
            or source_data.get("sourceStreamName")
            or "No Source"
        )

        # Discovered sources
        sources = await self.get_available_sources()
        if current_source and current_source != "No Source" and current_source not in sources:
            sources.insert(0, current_source)

        # MAC Address extraction
        mac_address = (
            info.get("EthernetMAC")
            or info.get("EthMac")
            or info.get("MACAddress")
            or info.get("MacAddress")
            or info.get("MAC")
            or info.get("mac")
            or "Unknown"
        )

        # Network config method (DHCP vs Static)
        network_mode = info.get("NetworkConfigMethod") or "DHCP"
        ip_address = info.get("IPAddress") or info.get("ip") or self.host
        netmask = info.get("Netmask") or "Unknown"
        gateway = info.get("GateWay") or info.get("Gateway") or "Unknown"

        # Model and firmware resolution (detects MINI, FLEX, PLAY, PLAY PRO, STUDIO)
        raw_model = str(info.get("Model") or info.get("model") or info.get("DeviceType") or "").upper()
        device_name = (
            info.get("DeviceName")
            or info.get("MyHostName")
            or info.get("HostName")
            or info.get("name")
            or "BirdDog Device"
        )

        if "MINI" in raw_model or "MINI" in device_name.upper():
            model = "MINI"
        elif "FLEX" in raw_model or "FLEX" in device_name.upper():
            model = "FLEX 4K"
        elif "PLAY PRO" in raw_model or "PLAY PRO" in device_name.upper():
            model = "PLAY PRO"
        elif "PLAY" in raw_model or "PLAY" in device_name.upper():
            model = "PLAY"
        elif "STUDIO" in raw_model or "STUDIO" in device_name.upper():
            model = "STUDIO"
        else:
            # Check if converter with enc-settings / dec-settings (e.g. BirdDog Mini)
            try:
                enc_check = await self._request("GET", "/enc-settings")
                if isinstance(enc_check, dict) and ("ndiaudio" in enc_check or "ndivideoq" in enc_check):
                    model = "MINI"
                else:
                    model = info.get("Model") or info.get("model") or "BirdDog Device"
            except Exception:
                model = info.get("Model") or info.get("model") or "BirdDog Device"

        firmware = info.get("Version") or info.get("firmware") or info.get("version") or "Unknown"

        # Operating mode (Decode vs Encode)
        final_op_mode = op_mode or ("Decode" if "PLAY" in model else "Encode")

        # Decoding active state
        is_decoding = current_source not in ("No Source", "Unknown", "None", "")

        return {
            "online": True,
            "host": self.host,
            "port": self.port,
            "device_name": device_name,
            "model": model,
            "firmware": firmware,
            "serial": info.get("Serial") or info.get("serialNumber") or f"bd_{self.host}",
            "mac_address": mac_address,
            "network_mode": network_mode,
            "operation_mode": final_op_mode,
            "ip_address": ip_address,
            "netmask": netmask,
            "gateway": gateway,
            "current_source": current_source,
            "available_sources": sources,
            "audio_muted": mute_state,
            "is_decoding": is_decoding,
        }
