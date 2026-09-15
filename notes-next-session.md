# Notes for Next Session: ha-birddog-ndi

## Immediate Next Steps
1. **User Verification**:
   - Have the user pull or redownload `v1.2.0` in HACS and restart Home Assistant.
   - Verify that non-BirdDog NDI streams are no longer discovered.
   - Test password change and confirm all entities display valid live data without any "Unknown" states.
2. **Dynamic Source Refresh Tuning**:
   - Observe real-world latency when switching NDI sources from `select.video_source`.
