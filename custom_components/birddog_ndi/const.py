"""Constants for the BirdDog Play NDI integration."""

DOMAIN = "birddog_ndi"

DEFAULT_NAME = "BirdDog Play"
DEFAULT_PORT = 8080
DEFAULT_SCAN_INTERVAL = 15  # seconds

CONF_HOST = "host"
CONF_PORT = "port"
CONF_NAME = "name"

# API Endpoints
ENDPOINT_ABOUT = "/about"
ENDPOINT_VERSION = "/version"
ENDPOINT_CONNECT_TO = "/connectTo"
ENDPOINT_REFRESH = "/refresh"
ENDPOINT_LIST = "/list"
ENDPOINT_AUDIO_GAIN = "/analogueaudiooutputgain"

# Device defaults
MANUFACTURER = "BirdDog"
DEFAULT_MODEL = "PLAY"
