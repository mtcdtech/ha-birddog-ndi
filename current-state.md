# Current State: ha-birddog-ndi

## Project Status
- **Status**: Scaffold initialized with complete API client, DataUpdateCoordinator, Config Flow, Sensor, Select, and Switch platforms.
- **GitHub Repository**: `mtcdtech/ha-birddog-ndi`
- **Domain**: `birddog_ndi`
- **Version**: 1.0.0

## Implemented Components
1. **API Client (`birddog_api.py`)**:
   - Asynchronous client using `aiohttp`.
   - Polling endpoints: `/about`, `/version`, `/connectTo` (current source), `/analogueaudiooutputgain` (or audio mute).
   - Control endpoints: POST `/connectTo` with `sourceName` to switch NDI stream, audio mute/unmute.
2. **Coordinator (`coordinator.py`)**:
   - Polling device every 15 seconds.
   - Robust offline detection and automatic recovery.
3. **Config Flow (`config_flow.py`)**:
   - UI configuration asking for Host/IP, Port (default 8080), and Device Name.
   - Connection test during setup to prevent invalid configurations.
4. **Entities**:
   - Sensors: Online Status, Connected NDI Source, Resolution/Format, IP Address, Firmware Version.
   - Select: Active NDI Source selector (supports discovered sources and manual stream entry).
   - Switch: Audio Mute toggle.
5. **HACS & HA Compliance**:
   - `hacs.json` configured for HACS custom repository distribution.
   - `manifest.json` compliant with Home Assistant 2024+ specifications (`iot_class: local_polling`).

## Known Assumptions & Environment
- Target hardware: BirdDog PLAY (NDI decoder) communicating over local HTTP REST API (port 8080 by default, fallback to port 80).
- Compatible with any Home Assistant installation (OS, Supervised, Container, Core).
