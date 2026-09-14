# BirdDog Play NDI - Home Assistant Integration

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![GitHub Release](https://img.shields.io/github/v/release/mtcdtech/ha-birddog-ndi)](https://github.com/mtcdtech/ha-birddog-ndi/releases)

A custom Home Assistant integration to monitor and control **BirdDog PLAY** NDI decoders and players over the local network.

---

## Features

- **Device Diagnostics & Health**:
  - Device online/offline state
  - Current IP address and firmware version
  - Device model & name
- **NDI Stream Monitoring & Control**:
  - Current connected NDI video source sensor
  - Active video source selector (`select` entity) to switch NDI decode streams
- **Audio Control**:
  - Audio mute switch (`switch` entity)
- **Native Home Assistant UI Setup**:
  - User-friendly configuration flow with pre-flight connection validation.
  - Efficient polling via `DataUpdateCoordinator`.

---

## Installation via HACS

1. Make sure [HACS](https://hacs.xyz) is installed in your Home Assistant.
2. In Home Assistant, open **HACS** $\rightarrow$ Click the **three dots** in the top right $\rightarrow$ Select **Custom repositories**.
3. Add the repository:
   - **Repository**: `https://github.com/mtcdtech/ha-birddog-ndi`
   - **Category**: `Integration`
4. Click **Add**, then find **BirdDog Play NDI** in HACS and click **Download**.
5. Restart Home Assistant.

---

## Manual Installation

1. Download the latest release from the [Releases](https://github.com/mtcdtech/ha-birddog-ndi/releases) page.
2. Copy the `birddog_ndi` folder into your Home Assistant `/config/custom_components/` directory:
   ```text
   /config/custom_components/birddog_ndi/
   ```
3. Restart Home Assistant.

---

## Configuration

1. In Home Assistant, navigate to **Settings** $\rightarrow$ **Devices & Services** $\rightarrow$ **Add Integration**.
2. Search for **BirdDog Play NDI**.
3. Enter your BirdDog PLAY's:
   - **Host or IP Address** (e.g. `192.168.1.120`)
   - **Port** (Default is `8080`, or `80` depending on your firmware version)
   - **Device Name** (Optional friendly name)
4. Submit to create the device and all associated entities.

---

## Entities Provided

| Platform | Entity | Description |
| :--- | :--- | :--- |
| `sensor` | `sensor.<name>_status` | Connection state (`online` / `offline`) |
| `sensor` | `sensor.<name>_current_source` | Currently active NDI source name |
| `sensor` | `sensor.<name>_ip_address` | IP address of the BirdDog device |
| `sensor` | `sensor.<name>_firmware` | Firmware version |
| `select` | `select.<name>_video_source` | Dropdown to switch NDI stream |
| `switch` | `switch.<name>_audio_mute` | Toggle audio mute |

---

## License

MIT License. Developed by MTCD Tech.
