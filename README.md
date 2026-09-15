<p align="center">
  <img src="icon.png" alt="BirdDog NDI Logo" width="160" height="160">
</p>

# BirdDog NDI - Home Assistant Integration

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![GitHub Release](https://img.shields.io/github/v/release/mtcdtech/ha-birddog-ndi)](https://github.com/mtcdtech/ha-birddog-ndi/releases)

A custom Home Assistant integration to monitor and control **BirdDog NDI** devices over your local network:
- **BirdDog PLAY & PLAY PRO**
- **BirdDog MINI** (HDMI $\leftrightarrow$ NDI Encoder/Decoder)
- **BirdDog FLEX 4K** (Flex 4K IN, Flex 4K OUT, Flex 4K Backpack)
- **BirdDog STUDIO**

---

## What's New in v1.3.1

- 🚫 **Duplicate Discovery Fixed**: Resolved Zeroconf mDNS re-discovering and prompting to configure BirdDog devices that were already added (fixed port 80/8080 unique_id discrepancy and added active host de-duplication).
- 🎨 **Official Component Icon**: Integrated custom high-resolution BirdDog green branding icon across HACS and repository metadata.

---

## What's New in v1.3.0

- 🌐 **Expanded Device Support**: Comprehensive support for **BirdDog MINI**, **FLEX 4K**, **PLAY**, **PLAY PRO**, and **STUDIO**.
- 🔓 **Adaptive Authentication**:
  - Automatically identifies open REST APIs on devices like the **BirdDog Mini** and **Flex 4K** that don't require web session logins.
  - Seamlessly applies session-cookie login for password-protected web interfaces like **BirdDog Play**.
  - Strict pre-validation: rejects incorrect passwords on protected devices before adding.
- 🔄 **Operation Mode Telemetry**: Added `sensor.<name>_operation_mode` to monitor whether dual-mode converters like the **Mini** and **Flex** are in **Decode** or **Encode** mode (`/operationmode`).

---

## Installation via HACS

1. Make sure [HACS](https://hacs.xyz) is installed in your Home Assistant.
2. In Home Assistant, open **HACS** $\rightarrow$ Click the **three dots** in the top right $\rightarrow$ Select **Custom repositories**.
3. Add the repository:
   - **Repository**: `https://github.com/mtcdtech/ha-birddog-ndi`
   - **Category**: `Integration`
4. Click **Add**, find **BirdDog NDI** in HACS, and click **Download** (`v1.3.0`).
5. Restart Home Assistant.

---

## Configuration

### Automatic Discovery (mDNS / Zeroconf)
When any BirdDog device is detected on your local network, Home Assistant will prompt:
> **"Discovered BirdDog Device"**

Click **Configure**, enter your password if required (or leave default `birddog`), and submit!

### Manual Setup
1. In Home Assistant, go to **Settings $\rightarrow$ Devices & Services $\rightarrow$ Add Integration**.
2. Search for **BirdDog NDI**.
3. Enter:
   - **Host or IP Address** (e.g. `192.168.1.120`)
   - **Port** (Default `8080`, fallback `80`)
   - **Password** (Default `birddog`, automatically skipped on open REST devices like Mini/Flex)
   - **Device Name** (Optional friendly name)

### Changing Settings
On an already added device, go to **Settings $\rightarrow$ Devices & Services $\rightarrow$ BirdDog NDI $\rightarrow$ Configure**. You can update the password or adjust the update interval (5–60s) directly.

---

## Entities Provided

| Platform | Entity | Description |
| :--- | :--- | :--- |
| `sensor` | `sensor.<name>_status` | Connection state (`Online` / `Offline`) |
| `sensor` | `sensor.<name>_current_source` | Currently active NDI source name |
| `sensor` | `sensor.<name>_operation_mode` | Active mode (`Decode` or `Encode`) for Mini/Flex |
| `sensor` | `sensor.<name>_ip_address` | Device IP address (attributes: `netmask`, `gateway`) |
| `sensor` | `sensor.<name>_mac_address` | Hardware MAC address |
| `sensor` | `sensor.<name>_network_mode` | Network configuration (`DHCP` or `Static`) |
| `sensor` | `sensor.<name>_firmware` | Firmware version |
| `sensor` | `sensor.<name>_model` | Detected hardware model (`MINI`, `FLEX 4K`, `PLAY`, `PLAY PRO`, `STUDIO`) |
| `binary_sensor` | `binary_sensor.<name>_decoding_active` | `on` when actively decoding a stream |
| `select` | `select.<name>_video_source` | Dropdown to switch active NDI stream |
| `switch` | `switch.<name>_audio_mute` | Toggle audio mute |
| `button` | `button.<name>_reboot` | Trigger hardware reboot |
| `button` | `button.<name>_restart_video` | Restart video engine |
| `button` | `button.<name>_refresh_sources` | Trigger NDI discovery scan |

---

## License

MIT License. Developed by MTCD Tech.
