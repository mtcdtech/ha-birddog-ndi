# Change Tracker: ha-birddog-ndi

## [2026-09-14] v1.1.0 - Zeroconf Auto-discovery, Authentication, Options Flow & Expanded Entities
- **Goal**: Resolve "unknown" entity states caused by BirdUI password protection, add Zeroconf discovery, and expose all decoder sensors and controls.
- **Root Cause of "Unknown" States**:
  - BirdDog Play requires authentication via `/login` with `auth_password` to access decoder data. Without a session cookie, requests were rejected or redirected to the login form.
- **Changes Implemented**:
  - `birddog_api.py`: Implemented session cookie jar and `login()` method posting `auth_password`. Added automatic re-authentication upon 401/403 or login redirection.
  - `config_flow.py`: Added password input (default `birddog`), Zeroconf mDNS discovery handlers (`_http._tcp.local.`, `_ndi._tcp.local.`, `_birddog._tcp.local.`), and an `OptionsFlowHandler` to update credentials without deleting the integration.
  - `manifest.json`: Added Zeroconf discovery hooks and bumped version to `1.1.0`.
  - Added new platforms: `binary_sensor.py` (Decoding Active) and `button.py` (Reboot, Restart Video, Refresh Sources).
  - Expanded `sensor.py`: Added Source IP/Port, Video Format, Bitrate, Failover Source, Transport Protocol, Screensaver Mode, and MAC Address.
  - Expanded `select.py`: Added Failover Source, Screen Saver Mode, and Transport Protocol selectors.
  - Expanded `switch.py`: Added Tally Light switch alongside Audio Mute.
  - Updated `tests/test_birddog.py` with full mock tests for auth, control endpoints, and rich data aggregation.
- **Validation**:
  - JSON validation clean.
  - Python byte compilation clean.
  - 6 unit tests passing.
  - Tagged and released `v1.1.0`.

## [2026-09-14] v1.0.0 - Initial Project Initialization
- Initial scaffold created with basic API client, DataUpdateCoordinator, Config Flow, Sensor, Select, and Switch platforms.
