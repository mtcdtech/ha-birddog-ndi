# Notes for Next Session: ha-birddog-ndi

## Immediate Next Steps
1. **User Verification on v1.3.8**:
   - Update to `v1.3.8` in HACS.
   - **CRITICAL**: Restart Home Assistant (`Settings` -> `System` -> `Restart`) to load the updated integration.
   - For connected BirdDog devices:
     - Test switching video sources in the dropdown: verify it immediately updates and stays locked to the chosen stream without reverting.
     - Verify sensors continuously update without freezing.
   - For BirdDog Mini at `192.168.5.83`:
     - Add device via IP `192.168.5.83`, port `8080` (or `80`), password `1400Frankford`.
     - Ensure Home Assistant's host machine has network IP reachability to the `192.168.5.0/24` subnet (inter-VLAN routing or Tailscale route).
