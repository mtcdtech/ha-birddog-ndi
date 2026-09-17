# Change Tracker: ha-birddog-ndi

## [2026-09-17] v1.3.7 - Fix Session Isolation for Numerical IPs, Auto Port Migration & Accurate Error Categorization
- **Root Causes Discovered**:
  1. *Numerical IP Cookie Dropping*: When `session = async_get_clientsession(self.hass)` was used, Home Assistant's default cookie jar operates with `unsafe=False`, which silently drops cookies for raw IP address targets (`192.168.5.83`).
  2. *Unreachable Devices Misreported as Auth Failures*: When network probes timed out or failed to connect, `check_auth_required()` previously defaulted to `self._auth_required = bool(self.password)`. Calling `login()` on an unreachable device subsequently failed and raised `BirdDogAuthError`, deceiving users into believing their password was rejected when the device was actually unreachable.
  3. *Un-migrated Port 80 in Existing Entries & Coordinator Polling*: Existing config entries saved with port 80 were never auto-corrected to port 8080 during polling or startup, causing repeated polling errors on port 80.
  4. *Outdated README on GitHub*: The repository `README.md` "What's New" section was not updated since v1.3.2.
- **Fixes Implemented**:
  - `config_flow.py`: Switched `BirdDogDevice` instances to dedicated sessions with `aiohttp.CookieJar(unsafe=True)` and guaranteed cleanup with `await device.close()`.
  - `birddog_api.py`:
    - In `check_auth_required()`: attached session token headers and raised `BirdDogConnectionError` when no endpoints are reachable.
    - In `fetch_all_data()`: added automatic `_async_probe_port_8080()` probe to switch port 80 to 8080 during polling.
  - `__init__.py`: Added startup port migration to auto-correct any existing config entry with port 80 to 8080 and persist the update in Home Assistant.
  - `README.md`: Backfilled and formatted all "What's New" sections from v1.3.3 through v1.3.7.
  - `tests/test_birddog.py`: Added test coverage for unreachable device connection error classification and auto-probing in `fetch_all_data` (24/24 tests passing).
- **Validation**:
  - Validated live against physical BirdDog Mini at `192.168.5.83` with password `1400Frankford`. Port auto-correction, login, and coordinator polling all succeed.

## [2026-09-17] v1.3.6 - Fix aiohttp Dual Set-Cookie Session Dropping & 302 Redirect Handling
- **Root Cause Discovered**:
  - The BirdDog web portal sends two `Set-Cookie` headers on successful login:
    1. `Set-Cookie: BirdDogSession=; Max-Age=0` (cookie clear)
    2. `Set-Cookie: BirdDogSession=<token>` (new session token)
    followed by HTTP 302 to `/dashboard`.
  - When `allow_redirects=True`, `aiohttp` evaluated the `Max-Age=0` cookie and cleared the cookie jar before following the redirect. The server saw no session cookie on `/dashboard` and redirected back to `/login`, tricking the integration into thinking authentication failed!
- **Fix**:
  - Set `allow_redirects=False` in `login()` to intercept and parse all `Set-Cookie` headers directly.
  - Filter out `Max-Age=0`, extract the real session token, and manually store it in `self._session_token` and the cookie jar.
  - Attach `Cookie: BirdDogSession=<token>` header to all subsequent requests.
  - Detect 302 redirect to non-login paths as verified successful authentication.
  - Validated live against `192.168.5.83` using password `1400Frankford`—`dev.login()` returns `True`, `dev.test_connection()` returns `True`, all telemetry and 7 NDI sources retrieved.

## [2026-09-17] v1.3.5 - Flow Context Fallback & Diagnostic Logging
- **Goal**: Fix persistent authentication failure on BirdDog Mini (firmware `BirdDog Mini NDI_4_V_3.6.3`, IP `192.168.5.83`) and expand telemetry and NDI source discovery.
- **Root Cause Analysis**:
  1. *Port 80 vs 8080 Separation*: Port 80 is exclusively the web management portal (Antmicro/BirdUI) protected by a web password. It returns an HTML `<form id="auth_form"` for every URL path and does not host the JSON REST API. Port 8080 is the actual BirdDog REST API (Express server), which is completely open and requires zero authentication.
  2. *Zeroconf Port Trap*: Zeroconf discovers `_http._tcp.local.` on port 80. `config_flow.py` previously stored port 80, causing Home Assistant to probe the Web UI on port 80, misinterpreting the HTML login form as a protected REST API, attempting a failed `/login` POST, and raising `BirdDogAuthError`.
  3. *Dictionary Source Mappings & MyHostName*: The Mini returns `"MyHostName"` instead of `"DeviceName"` in `/about`, and `/list` returns a dictionary whose keys are the stream names (`{"STREAM_NAME": "IP:PORT"}`) rather than an embedded `"sources"` list.
- **Changes Implemented**:
  - `birddog_api.py`:
    - Added `_async_probe_port_8080()`: when initialized with port 80 (or when port 80 serves an HTML login form), automatically tests port 8080 and redirects `self.port` to 8080.
    - Updated `check_auth_required()`: automatically upgrades to 8080, marks auth not required on open REST APIs.
    - Updated `get_available_sources()`: extracts `list(data.keys())` when `/list` returns dictionary mappings.
    - Updated `get_audio_mute()`: queries `/enc-settings` for `"ndiaudio"`.
    - Updated `fetch_all_data()`: extracts `"MyHostName"` as device name and identifies model `MINI`.
  - `config_flow.py`:
    - In `async_step_zeroconf`: normalizes discovered port from 80 to `DEFAULT_PORT` (8080).
    - In `async_step_user` and `async_step_zeroconf_confirm`: saves verified `device.port` in config entry data.
  - `manifest.json`: Bumped version to `1.3.4`.
  - `tests/test_birddog.py`: Added 4 unit tests covering auto-probe port upgrade, MyHostName resolution, dictionary source list parsing, and Zeroconf port normalization (22/22 tests passing).
- **Validation**:
  - 22 unit tests passing clean (0.067s).
  - Python byte compilation and JSON validation clean.
  - Live hardware probe against `192.168.5.83` confirmed port auto-correction, open auth detection, and full telemetry retrieval.

## [2026-09-16] v1.3.3 - Multi-Vector Zeroconf Deduplication & Dual-Service In-Progress Flow Suppression
- **Goal**: Completely eradicate repeat Zeroconf auto-discovery for already configured BirdDog devices.
- **Root Cause Analysis**:
  1. *Dual Service Advertisement*: BirdDog hardware broadcasts both `_http._tcp.local.` and `_birddog._tcp.local.`. Home Assistant spawned concurrent discovery flows for the same physical device. When the user configured one, the second flow remained orphaned in HA's active flow manager and was displayed as an unconfigured discovered device.
  2. *IPv6 vs IPv4 / Scope Blindspots*: When Zeroconf packets arrived over IPv6 (link-local `fe80::...%scope`), candidate hosts did not match IPv4 addresses stored in `entry.data[CONF_HOST]`. Furthermore, `discovery_info.ip_addresses` (plural) was not being inspected, and unresolvable `.local` hostnames were not matched against existing titles or MAC addresses.
  3. *Hardware Suffix & Name Matching*: Configured entries had titles like `BirdDog Play 94F8`, while Zeroconf announced `BirdDog-PLAY-94F8._http._tcp.local.`. Previous matching only checked exact host strings, missing normalized hardware names and 4-hex MAC suffixes.
- **Changes Implemented**:
  - `config_flow.py`:
    - Implemented multi-vector matching (`_is_match`, `_extract_discovery_info`, `_extract_entry_info`): checks IP addresses (including IPv6 zone-strip), hostnames, MAC address from TXT properties, legacy unique_ids, coordinator runtime MAC, and normalized hardware suffixes (e.g. `94f8`).
    - Added fast pass to evaluate direct matches in microseconds before performing any fallback DNS lookups.
    - Added `already_in_progress` check scanning `self._async_in_progress()` to suppress secondary flows when a device broadcasts both `_http` and `_birddog` services.
    - Set canonical `unique_id` to MAC or hostname or IP and called `_abort_if_unique_id_configured(updates={CONF_HOST: host})`.
  - `__init__.py`:
    - Updated `_async_dismiss_matching_discovery_flows` in `async_setup_entry` to scan all active discovery flows and abort any flow matching ANY configured device or coordinator data.
  - `tests/test_birddog.py`:
    - Added comprehensive unit tests covering IPv6 discovery with IPv4 in `ip_addresses`, hardware name suffix matching, in-progress flow deduplication, and genuine new device discovery (18/18 tests passing).
- **Validation**:
  - All 18 unit tests passed clean (0.032s).

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
