# Notes for Next Session: ha-birddog-ndi

## Immediate Next Steps
1. **Live User Verification on v1.3.3**:
   - Have user update to `v1.3.3` in HACS and reload the integration or restart Home Assistant.
   - Verify that all duplicate "Discovered" cards for already added BirdDog devices are cleared and never reappear.
   - Perform a hard browser refresh (Cmd+Shift+R or clear cached images) to ensure the newly added brand logo loads.
2. **Encode Mode Enhancements (Future)**:
   - For encoders (e.g. Flex 4K IN, Mini in Encode mode), add support for reading and changing NDI output stream names via `/enc-settings` or `/operation-configuration`.
