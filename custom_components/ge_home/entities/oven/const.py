import bidict

from homeassistant.components.water_heater import WaterHeaterEntityFeature
from gehomesdk import ErdOvenCookMode

SUPPORT_NONE = WaterHeaterEntityFeature(0)
GE_OVEN_SUPPORT = (WaterHeaterEntityFeature.OPERATION_MODE | WaterHeaterEntityFeature.TARGET_TEMPERATURE)

OP_MODE_OFF = "Off"
OP_MODE_BAKE = "Bake"
OP_MODE_CONVMULTIBAKE = "Conv. Multi-Bake"
OP_MODE_CONVBAKE = "Convection Bake"
OP_MODE_CONVROAST = "Convection Roast"
OP_MODE_COOK_UNK = "Unknown"
OP_MODE_PIZZA = "Frozen Pizza"
OP_MODE_FROZEN_SNACKS = "Frozen Snacks"
OP_MODE_BAKED_GOODS = "Baked Goods"
OP_MODE_FROZEN_PIZZA_MULTI = "Frozen Pizza Multi"
OP_MODE_FROZEN_SNACKS_MULTI = "Frozen Snacks Multi"
OP_MODE_BROIL_HIGH = "Broil High"
OP_MODE_BROIL_LOW = "Broil Low"
OP_MODE_PROOF = "Proof"
OP_MODE_WARM = "Warm"

OP_MODE_AIRFRY = "Air Fry"

UPPER_OVEN = "UPPER_OVEN"
LOWER_OVEN = "LOWER_OVEN"

COOK_MODE_OP_MAP = bidict.bidict({
    ErdOvenCookMode.NOMODE: OP_MODE_OFF,
    ErdOvenCookMode.CONVMULTIBAKE_NOOPTION: OP_MODE_CONVMULTIBAKE,
    ErdOvenCookMode.CONVBAKE_NOOPTION: OP_MODE_CONVBAKE,
    ErdOvenCookMode.CONVROAST_NOOPTION: OP_MODE_CONVROAST,
    ErdOvenCookMode.BROIL_LOW: OP_MODE_BROIL_LOW,
    ErdOvenCookMode.BROIL_HIGH: OP_MODE_BROIL_HIGH,
    ErdOvenCookMode.BAKE_NOOPTION: OP_MODE_BAKE,
    ErdOvenCookMode.PROOF_NOOPTION: OP_MODE_PROOF,
    ErdOvenCookMode.WARM_NOOPTION: OP_MODE_WARM,
    ErdOvenCookMode.FROZEN_PIZZA: OP_MODE_PIZZA,
    ErdOvenCookMode.FROZEN_SNACKS: OP_MODE_FROZEN_SNACKS,
    ErdOvenCookMode.BAKED_GOODS: OP_MODE_BAKED_GOODS,
    ErdOvenCookMode.FROZEN_PIZZA_MULTI: OP_MODE_FROZEN_PIZZA_MULTI,
    ErdOvenCookMode.FROZEN_SNACKS_MULTI: OP_MODE_FROZEN_SNACKS_MULTI,
    ErdOvenCookMode.AIRFRY: OP_MODE_AIRFRY
})

