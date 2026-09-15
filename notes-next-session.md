# Notes for Next Session: ha-birddog-ndi

## Immediate Next Steps
1. **Live User Verification on BirdDog Mini**:
   - Have the user update to `v1.3.0` in HACS and restart Home Assistant.
   - Add the BirdDog Mini and verify that Adaptive Authentication connects without error.
   - Confirm that `sensor.<name>_operation_mode` reports the correct mode (`Decode` or `Encode`).
2. **Encode Mode Enhancements (Future)**:
   - For encoders (e.g. Flex 4K IN, Mini in Encode mode), add support for reading and changing NDI output stream names via `/enc-settings` or `/operation-configuration`.
