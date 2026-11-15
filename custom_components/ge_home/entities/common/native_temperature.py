"""Temperature property names across Home Assistant releases.

HA 2026.11 renamed the climate and water heater temperature properties to
native_*. The old names warn there and stop working in 2027.11, while releases
before 2026.11 only read the old names. Entities implement native_* and the
base classes map the old names onto them when HA still needs those.
"""

from homeassistant.components.water_heater import WaterHeaterEntity

NATIVE_TEMPERATURES = hasattr(WaterHeaterEntity, "native_temperature_unit")
