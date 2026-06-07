"""Constants for the AR Duty Cycler integration."""

DOMAIN = "ar_duty_cycler"

PLATFORMS = ["switch", "number", "time", "select", "sensor"]

STORAGE_VERSION = 1

# Dispatcher signal (formatted with entry_id)
SIGNAL_UPDATE = DOMAIN + "_update_{}"

# Config / option keys
CONF_NAME = "name"
CONF_TARGET_ENTITY = "target_entity"
CONF_ON_DURATION = "on_duration"
CONF_OFF_DURATION = "off_duration"
CONF_WINDOW_START = "window_start"
CONF_WINDOW_END = "window_end"
CONF_PARK_STATE = "park_state"
CONF_START_PHASE = "start_phase"

# Defaults
DEFAULT_ON_DURATION = 10.0  # minutes
DEFAULT_OFF_DURATION = 10.0  # minutes
DEFAULT_WINDOW_START = "17:00:00"
DEFAULT_WINDOW_END = "22:00:00"
DEFAULT_PARK_STATE = "off"
DEFAULT_START_PHASE = "on"

# Phases / values
PHASE_ON = "on"
PHASE_OFF = "off"
STATE_OPTIONS = [PHASE_ON, PHASE_OFF]

# Status values surfaced by the status sensor
STATUS_IDLE = "idle"          # master switch off
STATUS_WAITING = "waiting"    # master on, currently outside the time window
STATUS_RUNNING_ON = "running_on"
STATUS_RUNNING_OFF = "running_off"
STATUS_OPTIONS = [
    STATUS_IDLE,
    STATUS_WAITING,
    STATUS_RUNNING_ON,
    STATUS_RUNNING_OFF,
]

MANUFACTURER = "ARSmartHome"
MODEL = "Duty Cycler"
