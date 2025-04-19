"""Constants for the FireBoard integration."""
from datetime import timedelta

DOMAIN = "fireboard"
SCAN_INTERVAL = timedelta(seconds=30)  # FireBoard API has a rate limit of 200 calls per hour

# Configuration
CONF_DEVICE_ID = "device_id"

# Attributes
ATTR_BATTERY = "battery"
ATTR_DEGREETYPE = "degree_type"
ATTR_HARDWARE_ID = "hardware_id"
ATTR_CHANNEL = "channel"
ATTR_DRIVE_ENABLED = "drive_enabled"
ATTR_DRIVE_TEMP = "drive_temp"
ATTR_DRIVE_OUTPUT = "drive_output"
ATTR_DRIVE_MODE = "drive_mode"

# Drive Modes
DRIVE_MODE_MANUAL = "manual"
DRIVE_MODE_AUTO = "auto"
DRIVE_MODE_OFF = "off"

# Units
TEMP_CELSIUS = "°C"
TEMP_FAHRENHEIT = "°F"

# API Endpoints
API_BASE_URL = "https://fireboard.io/api/v1"
API_LOGIN_URL = "https://fireboard.io/api/rest-auth/login/" 