# BirdDog Play NDI - Home Assistant Integration

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![GitHub Release](https://img.shields.io/github/v/release/mtcdtech/ha-birddog-ndi)](https://github.com/mtcdtech/ha-birddog-ndi/releases)

A custom Home Assistant integration to monitor and control **BirdDog PLAY** NDI decoders and players over the local network.

---

## What's New in v1.2.0

- 🎯 **Targeted Auto-Discovery**: Removed broad `_ndi._tcp.local.` so that Home Assistant **only** discovers actual BirdDog PLAY hardware, not other NDI feeds, cameras, or computers on your network.
- 🛡️ **Strict Password Pre-Validation**: Entering an incorrect password is now intercepted immediately before the device can be added, preventing failed setups and displaying a clear "Authentication failed" prompt.
- ✨ **Clean, 100% Populated Telemetry**: Removed camera-only entities (failover NDI, bitrate, transport protocol) that caused "Unknown" states on PLAY hardware. All sensors are now tailored directly to BirdDog PLAY capabilities.

---

## Installation via HACS

1. Make sure [HACS](https://hacs.xyz) is installed in your Home Assistant.
2. In Home Assistant, open **HACS** $\rightarrow$ Click the **three dots** in the top right $\rightarrow$ Select **Custom repositories**.
3. Add the repository:
   - **Repository**: `https://github.com/mtcdtech/ha-birddog-ndi`
   - **Category**: `Integration`
4. Click **Add**, then find **BirdDog Play NDI** in HACS and click **Download** (`v1.2.0`).
5. Restart Home Assistant.

---

## Configuration

### Automatic Discovery (mDNS / Zeroconf)
When a BirdDog PLAY is detected on your local network, Home Assistant will prompt:
> **"Discovered BirdDog PLAY"**

Click **Configure**, enter your device password (factory default is `birddog`), and submit!

### Manual Setup
1. In Home Assistant, go to **Settings $\rightarrow$ Devices & Services $\rightarrow$ Add Integration**.
2. Search for **BirdDog Play NDI**.
3. Enter:
   - **Host or IP Address** (e.g. `192.168.1.120`)
   - **Port** (Default `8080`, web portal on `80`)
   - **Password** (Default `birddog`)
   - **Device Name** (Optional friendly name)

### Changing Device Password or Polling
On an already added device, go to **Settings $\rightarrow$ Devices & Services $\rightarrow$ BirdDog Play NDI $\rightarrow$ Configure**. You can update the password or adjust the update interval (5–60s) directly.

---

## Entities Provided

| Platform | Entity | Description |
| :--- | :--- | :--- |
| `sensor` | `sensor.<name>_status` | Connection state (`Online` / `Offline`) |
| `sensor` | `sensor.<name>_current_source` | Currently active NDI source name |
| `sensor` | `sensor.<name>_ip_address` | Device IP address (attributes: `netmask`, `gateway`) |
| `sensor` | `sensor.<name>_mac_address` | Hardware MAC address |
| `sensor` | `sensor.<name>_network_mode` | Network configuration (`DHCP` or `Static`) |
| `sensor` | `sensor.<name>_firmware` | Firmware version |
| `sensor` | `sensor.<name>_model` | Device model (`PLAY`) |
| `binary_sensor` | `binary_sensor.<name>_decoding_active` | `on` when actively decoding a stream |
| `select` | `select.<name>_video_source` | Dropdown to switch active NDI stream |
| `switch` | `switch.<name>_audio_mute` | Toggle audio mute |
| `button` | `button.<name>_reboot` | Trigger hardware reboot |
| `button` | `button.<name>_restart_video` | Restart video decoding engine |
| `button` | `button.<name>_refresh_sources` | Trigger NDI discovery scan |

---

## License

MIT License. Developed by MTCD Tech.
