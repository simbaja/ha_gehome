from homeassistant.components.water_heater import WaterHeaterEntityFeature

SUPPORT_NONE = 0
GE_ADVANTIUM_WITH_TEMPERATURE = (WaterHeaterEntityFeature.OPERATION_MODE | WaterHeaterEntityFeature.TARGET_TEMPERATURE)
GE_ADVANTIUM = WaterHeaterEntityFeature.OPERATION_MODE
