from homeassistant.components.water_heater import WaterHeaterEntityFeature

GE_TOASTER_OVEN_SUPPORT = (
    WaterHeaterEntityFeature.OPERATION_MODE
    | WaterHeaterEntityFeature.TARGET_TEMPERATURE
)
