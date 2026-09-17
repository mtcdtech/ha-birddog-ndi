# Notes for Next Session: ha-birddog-ndi

## Immediate Next Steps
1. **User Verification on v1.3.7**:
   - Update to `v1.3.7` in HACS.
   - **CRITICAL**: Restart Home Assistant (Settings -> System -> Restart) to ensure Python loads the updated module into RAM.
   - If an existing failed device entry exists, reload or re-configure with password `1400Frankford`.
   - Verify device connects on port 8080 and populates telemetry + 7 NDI sources.
2. **Tailscale Subnet & Exit Node**:
   - Verify subnet routing from `mtcd-server` continues routing `192.168.5.0/24`.
3. **Encode Mode Enhancements (Future)**:
   - For encoders (e.g. Flex 4K IN, Mini in Encode mode), add support for reading and changing NDI output stream names via `/enc-settings`.
