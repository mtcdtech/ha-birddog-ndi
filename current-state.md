# Current State: ha-birddog-ndi

## Project Status
- **Status**: Release v1.3.9 tested and validated against live physical hardware (`192.168.5.61`, `192.168.5.62`, `192.168.5.63`, `192.168.5.83`), fixing source status accuracy, decoding active detection, and fallback source resolution.
- **GitHub Repository**: `mtcdtech/ha-birddog-ndi`
- **Domain**: `birddog_ndi`
- **Version**: 1.3.9

## Features in v1.3.9
1. **Real-Time WebSocket Telemetry (Port 6790)**:
   - Queries `ws://<host>:6790` directly for real-time hardware status metrics: `src_stat`, `vid_str_name`, `vid_res`, `vid_fr`, and bandwidth stats.
2. **True Decoding Detection**:
   - `binary_sensor.<name>_decoding_active` no longer relies solely on source name selection. It evaluates `src_stat` and `vid_res`: when status is `Initializing` or resolution is `0x0`, it accurately reports `Not running` (Off).
3. **Dedicated Source Status Sensor**:
   - Added `sensor.<name>_source_status` displaying exact hardware stream state (`Initializing`, `Connected`, `Online`, `No Source`) with video resolution and framerate attributes.
4. **Resilient Source Resolution Fallback**:
   - Resolved `NDI Foyer` and `NDI Fell. Hall` displaying `No Source` by falling back to live telemetry stream name (`vid_str_name`) and `/about` Format headers when `/connectTo` returns empty JSON.
5. **Dual-Dispatch Source Switching**:
   - Submits source change requests concurrently to both `/connectTo` REST API and `/videoset` HTML form parameters.

## Features in v1.3.8
1. **Prevented Source Reversion & Decoder Dropouts**:
   - Removed `/refresh` from routine `get_available_sources()` polling. Routine 15s `/refresh` calls triggered active NDI discovery scans on decoders, disrupting decoding and reverting active stream selections.
2. **Optimistic Source Switching with Settling Delay**:
   - In `select.py`, active state updates optimistically and introduces a 2-second settling delay before polling the hardware, avoiding race condition reads where `GET /connectTo` returned stale source names.
3. **Robust Coordinator Polling Error Handling**:
   - `_async_update_data()` in `coordinator.py` catches `BirdDogAPIError` and general exceptions, wrapping them in `UpdateFailed` so temporary HTTP errors or 404s do not crash the coordinator or freeze sensor entities.
4. **Bidirectional Port Adaptation**:
   - Extended port probing to automatically fall back and auto-migrate between port 8080 and port 80 in both directions.
5. **Cross-Subnet IP:Port Stream Mapping**:
   - Extracted IP:port from dictionary-keyed `/list` responses and provided `connectToIp` and `port` in `/connectTo` payloads.
6. **Audio Endpoint Caching**:
   - Dynamically caches working audio endpoints (`/enc-settings`, `/audiogain`, `/analogaudiosetup`) to prevent repeated 404 queries every polling interval.

## Features in v1.3.4
1. **Automatic Port 80-to-8080 REST API Redirection**:
   - Zeroconf mDNS announces `_http._tcp.local.` on web port 80. The BirdDog REST API is hosted on port 8080.
   - `config_flow.py` normalizes discovered port to `DEFAULT_PORT` (8080) and records verified `device.port` in config entries.
   - `birddog_api.py` includes `_async_probe_port_8080()` which automatically upgrades client port from 80 to 8080 if an active REST API is detected on 8080, preventing web portal login forms from blocking API access.
2. **BirdDog Mini Telemetry & Sources Expansion**:
   - Supports `"MyHostName"` as device name in `/about` (resolves `NDI-FellHall-Cam` on Mini).
   - In `get_available_sources()`, supports dictionary-keyed source mappings (`{"STREAM_NAME": "IP:PORT"}`) returned by BirdDog converters on `/list`.
   - In `get_audio_mute()`, queries `/enc-settings` for `"ndiaudio"` status.
   - Recognizes model `MINI` when `/enc-settings` or `/dec-settings` is active.

## Features in v1.3.3
1. **Multi-Vector Zeroconf Deduplication**:
   - Matches candidate devices across IP addresses (including IPv6 scope-stripped formats and full `ip_addresses` lists), hostnames, MAC address from TXT records, coordinator runtime data, and normalized 4-hex hardware suffixes (e.g. `94f8`).
2. **Dual-Service In-Progress Flow Suppression**:
   - Hardware broadcasting both `_http._tcp.local.` and `_birddog._tcp.local.` no longer spawns duplicate discovery flows. Detects active flows and aborts secondary flows with `already_in_progress`.
3. **Comprehensive Ghost Flow Purge**:
   - `_async_dismiss_matching_discovery_flows` purges all lingering discovery cards on Home Assistant startup and reload for any configured device.

## Features in v1.3.2
1. **Official Brand Assets in `brand/` Directory**:
   - Created `custom_components/birddog_ndi/brand/` containing all required Home Assistant brand files (`icon.png`, `icon@2x.png`, `logo.png`, `logo@2x.png`, `dark_icon.png`, `dark_logo.png`, etc.) ensuring the green BirdDog logo displays on Home Assistant integration cards, device pages, and dashboards.
2. **Automatic Ghost Discovery Dismissal**:
   - In `__init__.py`, `async_setup_entry` automatically scans `hass.config_entries.flow.async_progress_by_handler` and aborts any pending discovery flows matching configured devices, eliminating ghost "Discovered" cards from previous sessions upon startup/reload.
3. **Deep De-Duplication in Config Flow**:
   - Added `_is_device_already_configured` matching IP, resolvable hostnames, and legacy port IDs.
   - `async_step_zeroconf_confirm` now checks before displaying the form, instantly dismissing the card if clicked.

## Features in v1.3.1
1. **Duplicate Discovery Fix**:
   - Resolved Zeroconf discovery prompting to configure BirdDog devices that are already added.
   - Normalized `unique_id` to `host` and added active entry host checking (`entry.data[CONF_HOST] == host` and legacy unique_id matching).
2. **Official Branding Icon**:
   - Integrated custom high-resolution BirdDog green branding icon across repository root (`icon.png`, `logo.png`), component directory, and README header.

## Features in v1.3.0
1. **Multi-Device Hardware Support**:
   - BirdDog PLAY and PLAY PRO (Decoders)
   - BirdDog MINI (HDMI to NDI / NDI to HDMI Converter)
   - BirdDog FLEX 4K (Flex 4K IN, Flex 4K OUT, Flex 4K Backpack)
   - BirdDog STUDIO
2. **Adaptive Authentication Engine**:
   - `check_auth_required()` dynamically tests whether the target hardware has an open REST API (like Mini and Flex) or requires session authentication (like Play).
   - If open: connects with zero credentials needed, eliminating false "Authentication failed" errors on the Mini.
   - If protected: executes cookie-jar login and rejects invalid passwords before creating the entry.
3. **Operation Mode Telemetry**:
   - Added `sensor.<name>_operation_mode` reporting whether converters like the Mini and Flex are currently in `Decode` mode or `Encode` mode (`/operationmode`).
