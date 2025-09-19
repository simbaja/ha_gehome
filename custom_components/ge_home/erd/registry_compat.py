"""
SDK-agnostic registration for Haier hood ERD encoders/decoders.

Works with:
- Newer SDKs that expose gehomesdk.erd.erd_value_registry
- Older SDKs that only have per-appliance encoder/decoder registries
"""

import logging
from typing import Any

from gehomesdk.ge_appliance import GeAppliance

from .haier_hood_codes import (
    ERD_HAIER_HOOD_FAN_SPEED,
    ERD_HAIER_HOOD_LIGHT_LEVEL,
)
from .haier_hood_converters import (
    HaierHoodFanSpeedConverter,
    HaierHoodLightLevelConverter,
)

_LOGGER = logging.getLogger(__name__)

# ---- Global registration path (when available) ------------------------------

def _try_global_register() -> bool:
    try:
        # Preferred modern API (if your SDK exposes it)
        from gehomesdk.erd.erd_value_registry import register_erd_encoder, register_erd_decoder  # type: ignore

        register_erd_decoder(ERD_HAIER_HOOD_FAN_SPEED, HaierHoodFanSpeedConverter())
        register_erd_encoder(ERD_HAIER_HOOD_FAN_SPEED, HaierHoodFanSpeedConverter())

        register_erd_decoder(ERD_HAIER_HOOD_LIGHT_LEVEL, HaierHoodLightLevelConverter())
        register_erd_encoder(ERD_HAIER_HOOD_LIGHT_LEVEL, HaierHoodLightLevelConverter())

        _LOGGER.debug("GE Home: Registered Haier hood ERDs via global registry API")
        return True
    except Exception as ex:
        _LOGGER.warning("GE Home: No global ERD registry API (%s). Will patch per-appliance.", ex)
        return False


_GLOBAL_OK = _try_global_register()


def ensure_haier_hood_handlers_for_appliance(appliance: GeAppliance) -> None:
    """
    If the SDK doesn't have a global registry, attach our handlers directly to this appliance's
    encoder/decoder registries. Safe to call multiple times.
    """
    try:
        # Some SDKs expose ._encoder._registry and ._decoder._registry dicts
        enc_reg = getattr(getattr(appliance, "_encoder", None), "_registry", None)
        dec_reg = getattr(getattr(appliance, "_decoder", None), "_registry", None)

        if enc_reg is None or dec_reg is None:
            # Last-resort: older names (best effort)
            enc_reg = enc_reg or getattr(appliance, "_erd_encoder_registry", None)
            dec_reg = dec_reg or getattr(appliance, "_erd_decoder_registry", None)

        if enc_reg is None or dec_reg is None:
            raise RuntimeError("Could not locate appliance encoder/decoder registries")

        if ERD_HAIER_HOOD_FAN_SPEED not in dec_reg:
            dec_reg[ERD_HAIER_HOOD_FAN_SPEED] = HaierHoodFanSpeedConverter()
        if ERD_HAIER_HOOD_FAN_SPEED not in enc_reg:
            enc_reg[ERD_HAIER_HOOD_FAN_SPEED] = HaierHoodFanSpeedConverter()

        if ERD_HAIER_HOOD_LIGHT_LEVEL not in dec_reg:
            dec_reg[ERD_HAIER_HOOD_LIGHT_LEVEL] = HaierHoodLightLevelConverter()
        if ERD_HAIER_HOOD_LIGHT_LEVEL not in enc_reg:
            enc_reg[ERD_HAIER_HOOD_LIGHT_LEVEL] = HaierHoodLightLevelConverter()

    except Exception:
        _LOGGER.exception("GE Home: Failed to attach Haier hood handlers to appliance")
