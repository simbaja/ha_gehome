"""
SDK-agnostic registration for Haier hood ERD encoders/decoders.

Works with:
- Newer SDKs exposing gehomesdk.erd.erd_value_registry
- Older SDKs with module-level registries
- Very old SDKs with per-appliance encoder/decoder registries
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


# -------------------- helpers --------------------
def _erd_variants(key: Any) -> list[Any]:
    """
    Return a list of key variants to register against:
    - The value exactly as passed (ErdCode or str)
    - A normalized uppercase hex string (e.g. "0x5B13")
    - An ErdCode instance if the SDK exposes ErdCode
    """
    keys = [key]
    try:
        from gehomesdk.erd import ErdCode  # type: ignore
        as_str = str(key)
        if not isinstance(key, ErdCode):
            keys.append(ErdCode(as_str))
        keys.append(as_str.upper())
    except Exception:
        keys.append(str(key).upper())
    return keys


def _safe_put(reg: dict, code: Any, conv: Any) -> None:
    for k in _erd_variants(code):
        if k not in reg:
            reg[k] = conv


def _find_registry_dict(obj: Any) -> Optional[dict]:
    """Return the inner {ErdCode|str: converter} dict for many SDK layouts."""
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj

    # Try the most common attributes
    for attr in (
        "_registry",
        "registry",
        "_erd_encoder_registry",
        "_erd_decoder_registry",
        "_ErdEncoder__registry",  # name-mangled in some wheels
        "_ErdDecoder__registry",
    ):
        reg = getattr(obj, attr, None)
        if isinstance(reg, dict):
            return reg
    return None


def _get_encoder_decoder_regs(appliance: GeAppliance) -> tuple[Optional[dict], Optional[dict]]:
    """
    Probe several SDK layouts to find encoder/decoder registry dicts.
    """
    enc_reg = None
    dec_reg = None

    # Known attributes across SDK versions
    enc_candidates = [getattr(appliance, n, None) for n in ("_encoder", "_erd_encoder", "encoder")]
    dec_candidates = [getattr(appliance, n, None) for n in ("_decoder", "_erd_decoder", "decoder")]

    for cand in enc_candidates:
        enc_reg = _find_registry_dict(cand) or _find_registry_dict(getattr(cand, "_registry", None))
        if enc_reg:
            break

    for cand in dec_candidates:
        dec_reg = _find_registry_dict(cand) or _find_registry_dict(getattr(cand, "_registry", None))
        if dec_reg:
            break

    return enc_reg, dec_reg


#  global/module level registration 
def _try_global_register() -> bool:
    """Try all known global registry styles. Return True on success."""
    # 1) Function helpers (newest)
    try:
        from gehomesdk.erd.erd_value_registry import (  # type: ignore
            register_erd_encoder,
            register_erd_decoder,
        )

        conv_fan = HaierHoodFanSpeedConverter()
        conv_light = HaierHoodLightLevelConverter()

        register_erd_decoder(ERD_HAIER_HOOD_FAN_SPEED, conv_fan)
        register_erd_encoder(ERD_HAIER_HOOD_FAN_SPEED, conv_fan)
        register_erd_decoder(ERD_HAIER_HOOD_LIGHT_LEVEL, conv_light)
        register_erd_encoder(ERD_HAIER_HOOD_LIGHT_LEVEL, conv_light)

        _LOGGER.debug("GE Home: Registered Haier hood ERDs using function helpers")
        return True
    except Exception:
        pass

    # 2) Module-level dicts (older but common)
    try:
        from gehomesdk.erd import erd_value_registry as evr  # type: ignore

        # These names exist in some wheels
        enc = getattr(evr, "erd_value_encoder_registry", None)
        dec = getattr(evr, "erd_value_decoder_registry", None)
        if isinstance(enc, dict) and isinstance(dec, dict):
            _safe_put(dec, ERD_HAIER_HOOD_FAN_SPEED, HaierHoodFanSpeedConverter())
            _safe_put(enc, ERD_HAIER_HOOD_FAN_SPEED, HaierHoodFanSpeedConverter())
            _safe_put(dec, ERD_HAIER_HOOD_LIGHT_LEVEL, HaierHoodLightLevelConverter())
            _safe_put(enc, ERD_HAIER_HOOD_LIGHT_LEVEL, HaierHoodLightLevelConverter())
            _LOGGER.debug("GE Home: Registered Haier hood ERDs via module-level dicts")
            return True
    except Exception:
        pass

    return False


_GLOBAL_OK = _try_global_register()


#  per-appliance registration (fallback) 
def ensure_haier_hood_handlers_for_appliance(appliance: GeAppliance) -> None:
    """
    If the SDK doesn't have a global registry, attach our handlers directly to this
    appliance's encoder/decoder registries. Safe to call multiple times.
    """
    if _GLOBAL_OK:
        return

    try:
        enc_reg, dec_reg = _get_encoder_decoder_regs(appliance)
        if enc_reg is None or dec_reg is None:
            raise RuntimeError("Could not locate appliance encoder/decoder registries")

        _safe_put(dec_reg, ERD_HAIER_HOOD_FAN_SPEED, HaierHoodFanSpeedConverter())
        _safe_put(enc_reg, ERD_HAIER_HOOD_FAN_SPEED, HaierHoodFanSpeedConverter())

        _safe_put(dec_reg, ERD_HAIER_HOOD_LIGHT_LEVEL, HaierHoodLightLevelConverter())
        _safe_put(enc_reg, ERD_HAIER_HOOD_LIGHT_LEVEL, HaierHoodLightLevelConverter())

        _LOGGER.debug("GE Home: Patched appliance-level ERD handlers for Haier hood")
    except Exception:
        _LOGGER.exception("GE Home: Failed to attach Haier hood handlers to appliance")
