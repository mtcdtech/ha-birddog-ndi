# Notes for Next Session: ha-birddog-ndi

## Immediate Next Steps
1. **Live Network Testing**:
   - Test against a real BirdDog PLAY device on the local network.
   - Verify specific firmware responses for `/about`, `/version`, `/connectTo`, and audio endpoints.
2. **mDNS / Zeroconf Auto-Discovery**:
   - Add Zeroconf discovery (`_birddog._tcp.local` or `_http._tcp.local`) to `manifest.json` and `config_flow.py` so BirdDog Play units appear automatically in Home Assistant with a "Discovered" prompt.
3. **NDI Source Auto-Populate**:
   - If the device supports source discovery via `/refresh` or `/list`, parse dynamic sources to populate the `select` entity options automatically.
4. **Custom Lovelace Card (Optional)**:
   - Build a companion card to preview stream title, quick source buttons, and audio indicators.
