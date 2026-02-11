"""Constants for the Home Easy HVAC Local integration"""
# Base component constants
NAME = "Home Easy HVAC STABLE"
DOMAIN = "homeeasy_local_stable"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "1.2.0"
ATTRIBUTION = ""
ISSUE_URL = "https://github.com/danavorontsova/homeeasy_ha_local_stable/issues"

# Icons
ICON = "mdi:air-conditioner"

# Platforms
CLIMATE = "climate"
SELECT = "select"
SWITCH = "switch"
PLATFORMS = [CLIMATE, SELECT, SWITCH]

# Configuration and options
CONF_IP = "ip"

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
-------------------------------------------------------------------
"""
