"""Asynchronous client for interacting with BirdDog PLAY NDI devices."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


class BirdDogAPIError(Exception):
    """General BirdDog API exception."""


class BirdDogConnectionError(BirdDogAPIError):
    """Exception when unable to connect to BirdDog device."""


class BirdDogDevice:
    """Client representation of a BirdDog PLAY NDI device."""

    def __init__(
        self,
        host: str,
        port: int = 8080,
        session: aiohttp.ClientSession | None = None,
        timeout: int = 5,
    ) -> None:
        """Initialize the BirdDog device client."""
        self.host = host
        self.port = port
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session = session
        self._own_session = False

    @property
    def base_url(self) -> str:
        """Return the base URL of the BirdDog device."""
        return f"http://{self.host}:{self.port}"

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp client session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
            self._own_session = True
        return self._session

    async def close(self) -> None:
        """Close the session if created internally."""
        if self._own_session and self._session and not self._session.closed:
            await self._session.close()

    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Execute an async HTTP request to the device."""
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}"

        try:
            async with session.request(
                method,
                url,
                json=json_data,
                params=params,
                timeout=self.timeout,
            ) as response:
                if response.status >= 400:
                    text = await response.text()
                    raise BirdDogAPIError(
                        f"HTTP {response.status} from {endpoint}: {text}"
                    )

                content_type = response.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    return await response.json()
                text = await response.text()
                try:
                    import json
                    return json.loads(text)
                except Exception:
                    return text
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise BirdDogConnectionError(
                f"Failed to connect to BirdDog device at {self.host}:{self.port}: {err}"
            ) from err

    async def test_connection(self) -> bool:
        """Test if the device is reachable and responding."""
        try:
            # Try /about first, fallback to /version or /connectTo
            data = await self.get_device_info()
            return bool(data)
        except BirdDogAPIError:
            try:
                await self.get_current_source()
                return True
            except BirdDogAPIError:
                return False

    async def get_device_info(self) -> dict[str, Any]:
        """Fetch general device information from /about or /version."""
        try:
            data = await self._request("GET", "/about")
            if isinstance(data, dict):
                return data
        except BirdDogAPIError as err:
            _LOGGER.debug("Failed /about endpoint, trying /version: %s", err)

        try:
            data = await self._request("GET", "/version")
            if isinstance(data, dict):
                return data
            return {"Version": str(data).strip()}
        except BirdDogAPIError as err:
            _LOGGER.debug("Failed /version endpoint: %s", err)
            return {}

    async def get_current_source(self) -> dict[str, Any]:
        """Fetch current connected NDI source from /connectTo."""
        try:
            data = await self._request("GET", "/connectTo")
            if isinstance(data, dict):
                return data
            return {"sourceName": str(data).strip()}
        except BirdDogAPIError as err:
            _LOGGER.debug("Failed GET /connectTo: %s", err)
            return {}

    async def set_source(self, source_name: str) -> bool:
        """Switch NDI decode stream to source_name via POST /connectTo."""
        _LOGGER.info("Switching BirdDog %s NDI source to: %s", self.host, source_name)
        payload = {"sourceName": source_name}
        try:
            await self._request("POST", "/connectTo", json_data=payload)
            return True
        except BirdDogAPIError as err:
            _LOGGER.error("Failed to set NDI source to %s: %s", source_name, err)
            raise

    async def get_available_sources(self) -> list[str]:
        """Fetch list of discovered NDI sources if supported by firmware."""
        for endpoint in ("/list", "/refresh"):
            try:
                data = await self._request("GET", endpoint)
                if isinstance(data, list):
                    return [str(s) for s in data if s]
                if isinstance(data, dict):
                    # Some endpoints return {"sources": [...]}
                    sources = data.get("sources") or data.get("sourceList") or []
                    if isinstance(sources, list):
                        return [str(s) for s in sources if s]
            except BirdDogAPIError:
                continue
        return []

    async def get_audio_mute(self) -> bool:
        """Fetch audio mute status."""
        try:
            data = await self._request("GET", "/analogueaudiooutputgain")
            if isinstance(data, dict):
                return data.get("mute", False) or data.get("Mute", False)
        except BirdDogAPIError:
            pass
        return False

    async def set_audio_mute(self, mute: bool) -> bool:
        """Set audio mute state."""
        try:
            await self._request(
                "POST",
                "/analogueaudiooutputgain",
                json_data={"mute": mute},
            )
            return True
        except BirdDogAPIError as err:
            _LOGGER.debug("Audio mute setting failed or unsupported: %s", err)
            return False

    async def fetch_all_data(self) -> dict[str, Any]:
        """Fetch all device states in a single polling cycle."""
        info = await self.get_device_info()
        source_data = await self.get_current_source()
        mute_state = await self.get_audio_mute()

        current_source = (
            source_data.get("sourceName")
            or source_data.get("sourceStreamName")
            or source_data.get("source")
            or "Unknown"
        )

        sources = await self.get_available_sources()
        if current_source and current_source != "Unknown" and current_source not in sources:
            sources.insert(0, current_source)

        return {
            "online": True,
            "host": self.host,
            "port": self.port,
            "device_name": info.get("DeviceName") or info.get("name") or "BirdDog Play",
            "model": info.get("Model") or info.get("model") or "PLAY",
            "firmware": info.get("Version") or info.get("firmware") or info.get("version") or "Unknown",
            "serial": info.get("Serial") or info.get("serialNumber") or f"bd_{self.host}",
            "current_source": current_source,
            "available_sources": sources,
            "audio_muted": mute_state,
        }
