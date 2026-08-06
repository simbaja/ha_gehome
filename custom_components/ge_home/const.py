"""Constants for the gehome integration."""

DOMAIN = "ge_home"

EVENT_ALL_APPLIANCES_READY = 'all_appliances_ready'
CONNECTION_NOTIFICATION_ID = "ge_home_connection"
CONFIG_FLOW_VERSION = 4

# Device identifier options (used for entity unique_ids and friendly names)
CONF_DEVICE_IDENTIFIER = "device_identifier"
DEVICE_IDENTIFIER_SERIAL_OR_MAC = "serial_or_mac"
DEVICE_IDENTIFIER_MAC_OR_SERIAL = "mac_or_serial"
# Existing installs keep the historical serial-first behavior; new installs
# default to the more stable MAC-first behavior.
DEFAULT_DEVICE_IDENTIFIER_EXISTING = DEVICE_IDENTIFIER_SERIAL_OR_MAC
DEFAULT_DEVICE_IDENTIFIER_NEW = DEVICE_IDENTIFIER_MAC_OR_SERIAL

CONF_REFRESH_TOKEN = "refresh_token"

HA_REFRESH_INTERVAL = 60
STATE_UPDATE_INTERVAL = 30
CLIENT_START_TIMEOUT = 30
INITIAL_UPDATE_TIMEOUT = 10
VALIDATE_DATA_TIMEOUT = 10

MIN_RETRY_DELAY = 15
MAX_RETRY_DELAY = 1800
RECONNECT_JITTER = 0.2
PERSISTENT_RETRY_LOG_INTERVAL = 300
RETRY_OFFLINE_COUNT = 5
NOTIFY_AFTER_RETRIES = 5

SERVICE_SET_TIMER = "set_timer"
SERVICE_CLEAR_TIMER = "clear_timer"
SERVICE_SET_INT_VALUE = "set_int_value"
