"""Constants for the BirdDog Play NDI integration."""

DOMAIN = "birddog_ndi"

DEFAULT_NAME = "BirdDog Play"
DEFAULT_PORT = 8080
DEFAULT_PASSWORD = "birddog"
DEFAULT_SCAN_INTERVAL = 15  # seconds

CONF_HOST = "host"
CONF_PORT = "port"
CONF_NAME = "name"
CONF_PASSWORD = "password"
CONF_SCAN_INTERVAL = "scan_interval"

# API Endpoints
ENDPOINT_LOGIN = "/login"
ENDPOINT_ABOUT = "/about"
ENDPOINT_VERSION = "/version"
ENDPOINT_CONNECT_TO = "/connectTo"
ENDPOINT_REFRESH = "/refresh"
ENDPOINT_LIST = "/list"
ENDPOINT_AUDIO_GAIN = "/analogueaudiooutputgain"
ENDPOINT_ANALOG_SETUP = "/analogaudiosetup"
ENDPOINT_DECODE_STATUS = "/decodestatus"
ENDPOINT_DECODE_SETUP = "/decodesetup"
ENDPOINT_DECODE_TRANSPORT = "/decodeTransport"
ENDPOINT_VIDEO_OUTPUT = "/videooutputinterface"
ENDPOINT_REBOOT = "/reboot"
ENDPOINT_RESTART_VIDEO = "/restartPost"

# Device defaults
MANUFACTURER = "BirdDog"
DEFAULT_MODEL = "PLAY"
