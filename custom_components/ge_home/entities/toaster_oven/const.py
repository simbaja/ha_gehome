from homeassistant.components.water_heater import WaterHeaterEntityFeature

GE_TOASTER_OVEN_SUPPORT = (
    WaterHeaterEntityFeature.OPERATION_MODE
    | WaterHeaterEntityFeature.TARGET_TEMPERATURE
)

OP_MODE_AIR_FRY = "Air Fry"
OP_MODE_BAKE = "Bake"
OP_MODE_BROIL = "Broil"
OP_MODE_ROAST = "Roast"
OP_MODE_REHEAT = "Reheat"
OP_MODE_WARM = "Warm"
OP_MODE_SLOW_COOK = "Slow Cook"
OP_MODE_DEHYDRATE = "Dehydrate"
OP_MODE_PROOF = "Proof"
OP_MODE_COOKIE = "Cookie"
OP_MODE_FROZEN_PIZZA = "Frozen Pizza"
OP_MODE_BAGEL = "Bagel"
OP_MODE_TOAST = "Toast"
OP_MODE_CRISP_FINISH = "Crisp Finish"

TOASTER_OVEN_COOK_MODE_MAP = {
    OP_MODE_AIR_FRY: 0x00,
    OP_MODE_BAKE: 0x01,
    OP_MODE_BROIL: 0x02,
    OP_MODE_ROAST: 0x03,
    OP_MODE_REHEAT: 0x04,
    OP_MODE_WARM: 0x05,
    OP_MODE_SLOW_COOK: 0x06,
    OP_MODE_DEHYDRATE: 0x07,
    OP_MODE_PROOF: 0x08,
    OP_MODE_COOKIE: 0x09,
    OP_MODE_FROZEN_PIZZA: 0x0A,
    OP_MODE_BAGEL: 0x0B,
    OP_MODE_TOAST: 0x0C,
    OP_MODE_CRISP_FINISH: 0x0D,
}

TOASTER_OVEN_COOK_MODE_MAP_REVERSE = {
    value: key for key, value in TOASTER_OVEN_COOK_MODE_MAP.items()
}
