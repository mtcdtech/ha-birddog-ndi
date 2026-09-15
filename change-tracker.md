# Change Tracker: ha-birddog-ndi

## [2026-09-14] v1.3.0 - Multi-Device Hardware Support (Mini, Flex, Play Pro, Studio) & Adaptive Auth
- **Goal**: Expand support to BirdDog Mini, Flex 4K, Play Pro, and Studio, and fix authentication failure on the BirdDog Mini.
- **Root Cause on Mini**:
  - The BirdDog Mini exposes an open REST API on port `8080` without requiring `/login` session cookies. In `v1.2.0`, the client enforced a `/login` POST before probing, which failed with 404 on the Mini, mistakenly triggering an `invalid_auth` error.
- **Changes Implemented**:
  - `birddog_api.py`: Added `check_auth_required()` to adaptively determine if the device has an open REST API (Mini/Flex) or requires web portal login (Play/Play Pro). If open, connects immediately without auth errors. If protected, enforces login and rejects invalid passwords.
  - Added `/operationmode` support to track `Encode` vs `Decode` modes on converters like Mini and Flex.
  - Multi-model recognition: dynamically extracts and formats model names (`MINI`, `FLEX 4K`, `PLAY`, `PLAY PRO`, `STUDIO`).
  - Added `sensor.<name>_operation_mode` in `sensor.py`.
  - Updated `manifest.json` and `hacs.json` title to **BirdDog NDI**.
  - Updated test suite in `tests/test_birddog.py` with 9 passing tests covering open REST API devices, protected devices, operation mode detection, and controls.
- **Validation**:
  - JSON validation clean.
  - Python byte compilation clean.
  - 9 unit tests passing.
  - Tagged and released `v1.3.0`.

## [2026-09-14] v1.2.0 - Fix Autodiscovery Scope, Enforce Password Pre-Validation, and Eliminate Unknown Entities
- Fixed broad zeroconf discovery matching all NDI streams.
- Enforced password pre-validation.
- Removed camera-only endpoints to eliminate "Unknown" sensors on PLAY.

## [2026-09-14] v1.1.0 - Zeroconf Auto-discovery, Authentication, Options Flow & Expanded Entities
- Initial expansion with login sessions and discovery.

## [2026-09-14] v1.0.0 - Initial Project Initialization
- Initial scaffold created with basic API client, DataUpdateCoordinator, Config Flow, Sensor, Select, and Switch platforms.
