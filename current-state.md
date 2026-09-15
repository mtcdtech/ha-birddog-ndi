# Current State: ha-birddog-ndi

## Project Status
- **Status**: Release v1.1.0 ready and validated.
- **GitHub Repository**: `mtcdtech/ha-birddog-ndi`
- **Domain**: `birddog_ndi`
- **Version**: 1.1.0

## Features in v1.1.0
1. **Zeroconf Auto-Discovery**:
   - Matches `_http._tcp.local.`, `_ndi._tcp.local.`, and `_birddog._tcp.local.`.
   - Native discovery flow in HA with password prompt.
2. **BirdUI Authentication**:
   - `birddog_api.py` manages session cookies across requests.
   - Posts to `/login` with `auth_password`.
   - Auto-relogin on 401/403 or redirect to login.
3. **Options Flow**:
   - Users can update password and polling interval dynamically in HA UI.
4. **Platforms & Entities**:
   - **Sensors**: Status, Current NDI Source, Source IP, Source Port, Failover Source, Video Format, Bitrate, Transport Protocol, Screen Saver Mode, IP Address, MAC Address, Firmware Version.
   - **Binary Sensor**: Active Decoding state.
   - **Selects**: Active Video Source, Failover Source, Screen Saver Mode, Transport Protocol.
   - **Switches**: Audio Mute, Tally Light.
   - **Buttons**: Reboot Device, Restart Video Engine, Refresh NDI Sources.
