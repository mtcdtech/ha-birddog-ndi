# Project Instructions: BirdDog Play NDI Home Assistant Integration (`ha-birddog-ndi`)

## Architecture & Technology Stack
- **Target Platform**: Home Assistant (Integration Domain: `birddog_ndi`)
- **Distribution Method**: HACS (Home Assistant Community Store) custom repository
- **Language**: Python 3.12+ (AsyncIO, `aiohttp`)
- **Architecture Pattern**: Home Assistant `DataUpdateCoordinator` pattern with typed API client (`birddog_api.py`)
- **Target Hardware**: BirdDog PLAY (NDI Decoder / Player) and compatible BirdDog NDI decoders/converters

## Repository Structure
```
ha-birddog-ndi/
├── custom_components/
│   └── birddog_ndi/
│       ├── __init__.py          # Integration lifecycle, setup & unload
│       ├── manifest.json        # HA integration manifest
│       ├── const.py             # Constants (DOMAIN, defaults, intervals)
│       ├── birddog_api.py       # Asynchronous HTTP/REST client for BirdDog
│       ├── coordinator.py       # DataUpdateCoordinator for polling & caching
│       ├── config_flow.py       # UI configuration flow
│       ├── sensor.py            # Device & stream status sensors
│       ├── select.py            # NDI source selector
│       ├── switch.py            # Audio mute switch
│       ├── strings.json         # Translation schema
│       └── translations/
│           └── en.json          # English translation strings
├── hacs.json                    # HACS repository metadata
├── README.md                    # Installation & documentation
├── agent.md                     # This instructions file
├── current-state.md             # Active status and known details
├── notes-next-session.md        # Prioritized next steps
├── change-tracker.md            # Log of changes and fixes
└── tests/                       # Unit and mock tests
```

## Guidelines & Rules
1. **Async Everywhere**: Always use `aiohttp.ClientSession` and async methods. Never block the Home Assistant event loop.
2. **Resilience**: BirdDog devices may reboot or briefly disconnect during NDI switching. Handle timeouts, connection drops, and invalid responses gracefully without spamming error logs.
3. **Validation Before Push**: Verify JSON files with `python3 -m json.tool` and Python files with `python3 -m py_compile` before every commit.
4. **HACS Compatibility**: Maintain clean release tags (`vX.Y.Z`) on GitHub so HACS can track updates.
