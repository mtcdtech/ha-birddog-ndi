# Current State: ha-birddog-ndi

## Project Status
- **Status**: Release v1.2.0 ready and validated.
- **GitHub Repository**: `mtcdtech/ha-birddog-ndi`
- **Domain**: `birddog_ndi`
- **Version**: 1.2.0

## Changes in v1.2.0
1. **Targeted Zeroconf Discovery**:
   - Removed generic `_ndi._tcp.local.` and `*play*` patterns.
   - Restriced to `_http._tcp.local.` with `name: birddog*` and `_birddog._tcp.local.`.
   - Flow code strictly validates device name and hostname before initiating flow.
2. **Password Pre-validation**:
   - `login()` verifies HTTP response status, checks against failure markers and re-rendered login forms, and verifies session cookies.
   - `test_connection()` explicitly raises `BirdDogAuthError` on bad password.
   - Config flow displays `invalid_auth` and halts setup before device can be created with invalid credentials.
3. **Tailored PLAY Telemetry (No "Unknown" Entities)**:
   - Trimmed camera-only entities (failover NDI, bitrate, transport protocol) that caused permanent "Unknown" states on PLAY hardware.
   - Sensors: Status, Current NDI Source, IP Address, MAC Address, Network Mode, Firmware, Model.
   - Binary Sensor: Decoding Active.
   - Select: Video Source.
   - Switch: Audio Mute.
   - Buttons: Reboot Device, Restart Video Engine, Refresh NDI Sources.
