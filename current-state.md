# Current State: ha-birddog-ndi

## Project Status
- **Status**: Release v1.3.0 ready, tested, and validated.
- **GitHub Repository**: `mtcdtech/ha-birddog-ndi`
- **Domain**: `birddog_ndi`
- **Version**: 1.3.0

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
