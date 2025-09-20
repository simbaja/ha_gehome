"""
SDK-agnostic registration for Haier hood ERD encoders/decoders.

Works with:
- Newer SDKs exposing gehomesdk.erd.erd_value_registry
- Older SDKs with per-appliance encoder/decoder registries
"""
from __future__ import annotations

import logging
from typing import Any, Optional

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


def _try_global_register() -> bool:
    """Try the modern, global registry API if present."""
    try:
        # New-ish names in the SDK (function-style helpers)
        from gehomesdk.erd.erd_value_registry import (  # type: ignore
            register_erd_encoder,
            register_erd_decoder,
        )

        register_erd_decoder(ERD_HAIER_HOOD_FAN_SPEED, HaierHoodFanSpeedConverter())
        register_erd_encoder(ERD_HAIER_HOOD_FAN_SPEED, HaierHoodFanSpeedConverter())

        register_erd_decoder(ERD_HAIER_HOOD_LIGHT_LEVEL, HaierHoodLightLevelConverter())
        register_erd_encoder(ERD_HAIER_HOOD_LIGHT_LEVEL, HaierHoodLightLevelConverter())

        _LOGGER.debug("GE Home: Registered Haier hood ERDs via global registry API")
        return True
    except Exception as ex:
        _LOGGER.debug("GE Home: No global ERD registry API (%s). Will patch per-appliance.", ex)
        return False


_GLOBAL_OK = _try_global_register()


def _find_registry_dict(obj: Any) -> Optional[dict]:
    """Return the inner {ErdCode|str: converter} dict from many possible SDK layouts."""
    if obj is None:
        return None

    # Direct dict
    if isinstance(obj, dict):
        return obj

    # Common attribute spellings
    for attr in ("_registry", "registry", "_erd_encoder_registry", "_erd_decoder_registry"):
        reg = getattr(obj, attr, None)
        if isinstance(reg, dict):
            return reg

    return None


def _get_encoder_decoder_regs(appliance: GeAppliance) -> tuple[Optional[dict], Optional[dict]]:
    """Probe multiple SDK layouts to find encoder/decoder registry dicts."""
    enc_candidates = [getattr(appliance, name, None) for name in ("_encoder", "_erd_encoder", "encoder")]
    dec_candidates = [getattr(appliance, name, None) for name in ("_decoder", "_erd_decoder", "decoder")]

    enc_reg = None
    dec_reg = None

    for cand in enc_candidates:
        enc_reg = _find_registry_dict(cand) or _find_registry_dict(getattr(cand, "_registry", None))
        if enc_reg:
            break

    for cand in dec_candidates:
        dec_reg = _find_registry_dict(cand) or _find_registry_dict(getattr(cand, "_registry", None))
        if dec_reg:
            break

    return enc_reg, dec_reg


def ensure_haier_hood_handlers_for_appliance(appliance: GeAppliance) -> None:
    """
    If the SDK doesn't have a global registry, attach our handlers directly to this appliance's
    encoder/decoder registries. Safe to call multiple times.
    """
    if _GLOBAL_OK:
        return  # already globally handled

    try:
        enc_reg, dec_reg = _get_encoder_decoder_regs(appliance)
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

        _LOGGER.debug("GE Home: Patched appliance-level ERD handlers for Haier hood")

    except Exception:
        _LOGGER.exception("GE Home: Failed to attach Haier hood handlers to appliance")
