# Notes for Next Session: ha-birddog-ndi

## Immediate Next Steps
1. **Live User Verification on v1.3.4**:
   - Have user update to `v1.3.4` in HACS and reload the integration or restart Home Assistant.
   - Verify that the BirdDog Mini (`192.168.5.83`, `NDI-FellHall-Cam`) is discovered or added without any authentication error.
   - Verify that all discovered NDI sources (`AVTEAMMACSTUDIO.LOCAL (Foyer)`, `AVTEAMMACSTUDIO.LOCAL (Nursery)`, `BIRDDOG-4951C (HDMI)`, etc.) populate properly in the source select entity.
2. **Tailscale Exit Node**:
   - Confirm route approval in the Tailscale admin console (`login.tailscale.com/admin/machines`) for `av-team-mac-studio` or `mtcd-server` so exit routing or subnet routing works directly from external devices.
3. **Encode Mode Enhancements (Future)**:
   - For encoders (e.g. Flex 4K IN, Mini in Encode mode), add support for reading and changing NDI output stream names via `/enc-settings`.
