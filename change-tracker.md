# Change Tracker: ha-birddog-ndi

## [2026-09-14] Initial Project Initialization (v1.0.0)
- **Goal**: Create a clean, HACS-ready Home Assistant custom integration for BirdDog PLAY NDI decoders.
- **Components Added**:
  - `custom_components/birddog_ndi/`: Complete core integration with `__init__.py`, `birddog_api.py`, `coordinator.py`, `config_flow.py`, `sensor.py`, `select.py`, and `switch.py`.
  - `manifest.json` and `hacs.json` configuration for HACS custom repository distribution.
  - UI translations in `strings.json` and `translations/en.json`.
  - Mock test suite in `tests/test_birddog.py` validating API responses and state mapping.
- **Validation**:
  - JSON syntax validated via `python3 -m json.tool`.
  - Python byte compilation verified via `python3 -m py_compile`.
  - Unit tests passed.
