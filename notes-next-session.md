# Notes for Next Session: ha-birddog-ndi

## Immediate Next Steps
1. **User Testing with Live Device**:
   - Have the user upgrade the HACS integration to `v1.1.0`.
   - In Home Assistant, open the device settings $\rightarrow$ Configure $\rightarrow$ confirm/set the password.
   - Verify that previously "unknown" sensors now report live telemetry.
2. **Dynamic NDI Source List Optimization**:
   - If the BirdDog firmware version returns an empty list from `/list`, monitor if `/refresh` requires a delay before sources populate.
3. **Custom Lovelace Card (Future Milestone)**:
   - Build a sleek dashboard card showing current stream thumbnail/preview, quick-switch buttons, and bitrate indicators.
