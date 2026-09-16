# Change Tracker: ha-birddog-ndi

## [2026-09-16] v1.3.2 - Official Brand Directory Integration & Automatic Discovery Dismissal
- **Goal**: Fix missing icon/logo on Home Assistant device pages and eliminate lingering "Discovered" cards for already-configured BirdDog devices.
- **Root Cause Analysis**:
  1. *Missing Brand Icon*: Home Assistant core does not read brand icons from the integration root (`custom_components/<domain>/icon.png`). It strictly expects a dedicated `brand/` directory inside the integration folder containing `icon.png`, `icon@2x.png`, `logo.png`, `dark_icon.png`, etc., served via `/api/brands/integration/birddog_ndi/`.
  2. *Discovered Cards Still Showing*: When devices were discovered in previous sessions, Home Assistant stored active discovery flows in its persistent flow manager (`core.config_entries`). Those pending flows remained on the dashboard across restarts unless aborted or dismissed. Furthermore, `async_step_zeroconf_confirm` displayed the password prompt before checking if the device was already added.
- **Changes Implemented**:
  - Created `custom_components/birddog_ndi/brand/` with all required image variants (`icon.png`, `icon@2x.png`, `logo.png`, `logo@2x.png`, `dark_icon.png`, `dark_icon@2x.png`, `dark_logo.png`, `dark_logo@2x.png`).
  - `__init__.py`: Added automatic dismissal in `async_setup_entry` that scans `hass.config_entries.flow.async_progress_by_handler(DOMAIN)` and aborts any stale discovery flows matching configured devices upon startup or reload.
  - `config_flow.py`: Implemented `_is_device_already_configured` with candidate host matching (IP, resolvable hostname, and port variants) and added immediate abort check to `async_step_zeroconf_confirm`.
  - Added unit test in `tests/test_birddog.py` validating `async_step_zeroconf_confirm` abort (14/14 tests passing).
- **Validation**:
  - Python byte compilation clean.
  - JSON schema validation clean.
  - 14/14 unit tests passed (0.021s).

## [2026-09-15] v1.3.1 - Fix Duplicate Discovery Prompting and Integrate Official Branding Icon
- **Goal**: Prevent Home Assistant from re-discovering and repeatedly prompting to add BirdDog devices that are already configured, and integrate official BirdDog green icon branding.
- **Root Cause of Duplicate Discovery**:
  - Zeroconf mDNS broadcasts `_http._tcp.local.` on port `80`.
  - Manual configuration (or default API setup) uses port `8080`.
  - Previously, `config_flow.py` set `unique_id` to `f"{host}:{port}"`. Because `192.168.1.50:80` != `192.168.1.50:8080`, Home Assistant did not recognize the device was already added.
- **Changes Implemented**:
  - `config_flow.py`: Normalized `unique_id` to `host` (IP address) across both manual and Zeroconf flows.
  - Added comprehensive de-duplication: iterates over `self._async_current_entries()` checking both `entry.data[CONF_HOST] == host` and legacy unique IDs (`{host}:80`, `{host}:8080`), immediately aborting with `already_configured`.
  - Also added de-duplication check in `async_step_zeroconf_confirm`.
  - Added official BirdDog green icon: `icon.png` and `logo.png` in repository root, `custom_components/birddog_ndi/icon.png`, and updated `README.md` header.
  - Added 4 new unit tests in `tests/test_birddog.py` (total 13/13 passing).
- **Validation**:
  - Python byte compilation clean.
  - JSON schema clean.
  - 13/13 unit tests passed (0.017s).

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
