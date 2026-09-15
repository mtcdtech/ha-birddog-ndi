# BirdDog Play NDI - Home Assistant Integration

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![GitHub Release](https://img.shields.io/github/v/release/mtcdtech/ha-birddog-ndi)](https://github.com/mtcdtech/ha-birddog-ndi/releases)

A custom Home Assistant integration to monitor and control **BirdDog PLAY** NDI decoders and players over the local network.

---

## What's New in v1.1.0

- 🚀 **Zeroconf Auto-Discovery**: Home Assistant automatically discovers BirdDog PLAY units on your local network (`_http._tcp.local.`, `_ndi._tcp.local.`, `_birddog._tcp.local.`).
- 🔐 **BirdUI Authentication Support**: Full session-based cookie login support via `/login` with configurable password (default `birddog`).
- ⚙️ **Options Flow**: Update your device password or adjust polling interval at any time without removing the integration.
- 🎛️ **Expanded Telemetry & Controls**:
  - **Sensors**: Active Source, Failover Source, Source IP & Port, Video Format/Resolution, Bitrate, Transport Protocol, Screen Saver Mode, IP, MAC Address, Firmware.
  - **Binary Sensor**: Decoding Active indicator.
  - **Selects**: Active Video Source, Failover Source, Screen Saver Mode, Transport Protocol (TCP/UDP/Multicast).
  - **Switches**: Audio Mute, Tally Light.
  - **Buttons**: Reboot Device, Restart Video Engine, Refresh NDI Sources.

---

## Installation via HACS

1. Make sure [HACS](https://hacs.xyz) is installed in your Home Assistant.
2. In Home Assistant, open **HACS** $\rightarrow$ Click the **three dots** in the top right $\rightarrow$ Select **Custom repositories**.
3. Add the repository:
   - **Repository**: `https://github.com/mtcdtech/ha-birddog-ndi`
   - **Category**: `Integration`
4. Click **Add**, then find **BirdDog Play NDI** in HACS and click **Download** (`v1.1.0`).
5. Restart Home Assistant.

---

## Configuration

### Automatic Discovery (mDNS / Zeroconf)
When a BirdDog PLAY is powered on your local network, Home Assistant will prompt:
> **"Discovered BirdDog PLAY"**

Click **Configure**, enter your device password (default is `birddog`), and submit!

### Manual Setup
1. In Home Assistant, go to **Settings $\rightarrow$ Devices & Services $\rightarrow$ Add Integration**.
2. Search for **BirdDog Play NDI**.
3. Enter:
   - **Host or IP Address** (e.g. `192.168.1.120`)
   - **Port** (Default `8080`, fallback `80`)
   - **Password** (Default `birddog`)
   - **Device Name** (Optional friendly name)

### Changing Device Password or Polling
On an already added device, go to **Settings $\rightarrow$ Devices & Services $\rightarrow$ BirdDog Play NDI $\rightarrow$ Configure**. You can change the password or adjust the update interval (5–60s) directly.

---

## Entities Provided

| Platform | Entity | Description |
| :--- | :--- | :--- |
| `sensor` | `sensor.<name>_status` | Connection state (`online` / `offline`) |
| `sensor` | `sensor.<name>_current_source` | Currently active NDI source name |
| `sensor` | `sensor.<name>_source_ip` | IP of active NDI sender |
| `sensor` | `sensor.<name>_source_port` | Port of active NDI sender |
| `sensor` | `sensor.<name>_failover_source` | Failover NDI source name |
| `sensor` | `sensor.<name>_video_format` | HDMI output resolution / format |
| `sensor` | `sensor.<name>_bitrate` | Active decode bitrate |
| `sensor` | `sensor.<name>_transport` | Transport protocol (TCP, UDP, Multicast) |
| `sensor` | `sensor.<name>_screensaver` | Current screen saver mode |
| `sensor` | `sensor.<name>_ip_address` | Device IP address |
| `sensor` | `sensor.<name>_mac_address` | Device MAC address |
| `sensor` | `sensor.<name>_firmware` | Firmware version |
| `binary_sensor` | `binary_sensor.<name>_decoding_active` | `on` when actively decoding a stream |
| `select` | `select.<name>_video_source` | Dropdown to switch active NDI stream |
| `select` | `select.<name>_failover_source` | Dropdown to set failover NDI stream |
| `select` | `select.<name>_screensaver_mode` | Screen saver mode (Logo, Black, ScreenSaver) |
| `select` | `select.<name>_transport_protocol` | Transport protocol (TCP, UDP, Multicast) |
| `switch` | `switch.<name>_audio_mute` | Toggle audio mute |
| `switch` | `switch.<name>_tally` | Toggle Tally light indicator |
| `button` | `button.<name>_reboot` | Trigger hardware reboot |
| `button` | `button.<name>_restart_video` | Restart video decoding engine |
| `button` | `button.<name>_refresh_sources` | Refresh discovered NDI sources |

---

## License

MIT License. Developed by MTCD Tech.
