# Notes for Next Session: ha-birddog-ndi

## Immediate Next Steps
1. **User Verification on v1.3.9**:
   - Update to `v1.3.9` in HACS.
   - Restart Home Assistant (`Settings` -> `System` -> `Restart`) to load the updated component.
   - For `Ndi-Nursery` (`192.168.5.63`):
     - Check `Ndi-Nursery Decoding Active`: should show `Not running` (Off) while in `Initializing` state.
     - Check new `Ndi-Nursery Source Status` sensor: shows `Initializing` (mirroring the web page header).
     - Once the transmitter (`AVTEAMMACSTUDIO` on `192.168.5.78:5961`) is powered on / streaming, verify the status transitions to `Connected`/`Online` and `Decoding Active` turns to `Running`.
   - For `NDI Foyer` (`192.168.5.61`) and `NDI Fell. Hall` (`192.168.5.62`):
     - Verify `Current NDI Source` shows `AVTEAMMACSTUDIO (Foyer-NDI)` and `AVTEAMMACSTUDIO (Nursery-NDI)` rather than `No Source`.
   - For video source selection:
     - Verify dual-path switching (`/connectTo` and `/videoset`) switches streams smoothly.
