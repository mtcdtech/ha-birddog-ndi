# Change Tracker: ha-birddog-ndi

## [2026-09-14] v1.2.0 - Fix Autodiscovery Scope, Enforce Password Pre-Validation, and Eliminate Unknown Entities
- **Goal**:
  1. Fix autodiscovery discovering all arbitrary NDI streams across the network.
  2. Detect incorrect passwords before the device is added.
  3. Fix entities showing "Unknown" by tailoring entities specifically to BirdDog PLAY hardware.
- **Root Causes & Solutions**:
  1. *Autodiscovery flood*: `manifest.json` included generic `_ndi._tcp.local.` and `*play*`. Removed these broad matchers and restricted discovery to `_http._tcp.local.` with `name: birddog*` and `_birddog._tcp.local.`, plus strict filtering in `async_step_zeroconf`.
  2. *Password acceptance bug*: `POST /login` on BirdUI returns HTTP 200 with the login form re-rendered when a password is wrong. Added checks for re-rendered form elements and failure markers, and verified session persistence. `test_connection()` now raises `BirdDogAuthError` explicitly on bad password, which `config_flow` catches to show `invalid_auth`.
  3. *Unknown entities*: Camera-only features (`/decodestatus`, `/decodeTransport`, `/connectTo?location=DecoderFailOver`, etc.) do not exist on BirdDog PLAY hardware. Removed these unsupported entities and focused on PLAY's native capabilities (Status, Current Source, IP, MAC Address, Network Mode, Firmware, Model, Decoding Active, Audio Mute, Reboot, Restart Video, Refresh Sources).
- **Validation**:
  - JSON validation clean.
  - Python byte compilation clean.
  - 8 unit tests passing.
  - Tagged and released `v1.2.0`.

## [2026-09-14] v1.1.0 - Zeroconf Auto-discovery, Authentication, Options Flow & Expanded Entities
- Initial expansion with login sessions and discovery.

## [2026-09-14] v1.0.0 - Initial Project Initialization
- Initial scaffold created with basic API client, DataUpdateCoordinator, Config Flow, Sensor, Select, and Switch platforms.
