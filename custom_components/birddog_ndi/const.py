"""Constants for the BirdDog NDI integration."""

DOMAIN = "birddog_ndi"

DEFAULT_NAME = "BirdDog Device"
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
ENDPOINT_OPERATION_MODE = "/operationmode"
ENDPOINT_REFRESH = "/refresh"
ENDPOINT_LIST = "/list"
ENDPOINT_AUDIO_GAIN = "/analogueaudiooutputgain"
ENDPOINT_ANALOG_SETUP = "/analogaudiosetup"
ENDPOINT_REBOOT = "/reboot"
ENDPOINT_RESTART_VIDEO = "/restartPost"

# Device defaults
MANUFACTURER = "BirdDog"
DEFAULT_MODEL = "Device"
