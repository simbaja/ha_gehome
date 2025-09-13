# Mapping between named speeds and their ERD code values for the Haier hood
FAN_SPEED_MAP = {
    "Off": 0,
    "Low": 1,
    "Medium": 2,
    "High": 3,
    "Boost": 4,
}

# Creates a reverse mapping to easily find the name for a given value
FAN_SPEED_MAP_REVERSE = {v: k for k, v in FAN_SPEED_MAP.items()}