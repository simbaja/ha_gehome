"""
SDK-agnostic registration for Haier hood ERD encoders/decoders.

Works with:
- Newer SDKs (object or function registries)
- Older SDKs with per-appliance encoder/decoder registries
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from gehomesdk.ge_appliance import GeAppliance

from .haier_hood_codes import (
    ERD_HAIER_HOOD_FAN_SPEED,
    ERD_HAIER_HOOD_LIGHT_LEVEL,
    ERD_HAIER_HOOD_FAN_SPEED_INT,
    ERD_HAIER_HOOD_LIGHT_LEVEL_INT,
    ERD_HAIER_HOOD_FAN_SPEED_STR,
    ERD_HAIER_HOOD_LIGHT_LEVEL_STR,
)
from .haier_hood_converters import (
    HaierHoodFanSpeedConverter,
    HaierHoodLightLevelConverter,
)

_LOGGER = logging.getLogger(__name__)


def _register_into_mapping(mapping: dict, keys: list[Any], conv: Any) -> None:
    for k in keys:
        mapping[k] = conv


def _global_register_all_variants() -> bool:
    """
    Try multiple global APIs and register BOTH numeric and string keys.
    Returns True if any succeeded (even partially).
    """
    ok_any = False

    # A) Function helpers (some SDK builds)
    try:
        from gehomesdk.erd.erd_value_registry import (  # type: ignore
            register_erd_encoder,
            register_erd_decoder,
        )

        for (int_code, str_code, conv) in [
            (ERD_HAIER_HOOD_FAN_SPEED_INT, ERD_HAIER_HOOD_FAN_SPEED_STR, HaierHoodFanSpeedConverter()),
            (ERD_HAIER_HOOD_LIGHT_LEVEL_INT, ERD_HAIER_HOOD_LIGHT_LEVEL_STR, HaierHoodLightLevelConverter()),
        ]:
            # numeric + both hex string casings
            for key in (int_code, str_code, str_code.lower()):
                register_erd_decoder(key, conv)
                register_erd_encoder(key, conv)
        _LOGGER.debug("GE Home: Registered Haier hood ERDs via function-style registry")
        ok_any = True
    except Exception:
        pass

    # B) Object registry (ERD_VALUE_REGISTRY) with .register or ._registry
    try:
        try:
            from gehomesdk.erd.erd_value_registry import ERD_VALUE_REGISTRY as REG  # type: ignore
        except Exception:
            from gehomesdk.erd.erd_value_registry import ErdValueRegistry as REG  # type: ignore

        backing = getattr(REG, "_registry", None)
        has_register = hasattr(REG, "register")

        def _do_reg(key: Any, conv: Any):
            nonlocal ok_any
            try:
                if has_register:
                    REG.register(key, conv)
                elif isinstance(backing, dict):
                    backing[key] = conv
                else:
                    return
                ok_any = True
            except Exception:
                pass

        for (int_code, str_code, conv) in [
            (ERD_HAIER_HOOD_FAN_SPEED_INT, ERD_HAIER_HOOD_FAN_SPEED_STR, HaierHoodFanSpeedConverter()),
            (ERD_HAIER_HOOD_LIGHT_LEVEL_INT, ERD_HAIER_HOOD_LIGHT_LEVEL_STR, HaierHoodLightLevelConverter()),
        ]:
            for key in (int_code, str_code, str_code.lower(), ERD_HAIER_HOOD_FAN_SPEED, ERD_HAIER_HOOD_LIGHT_LEVEL):
                _do_reg(key, conv)

        if ok_any:
            _LOGGER.debug("GE Home: Registered Haier hood ERDs via object-style registry")
    except Exception:
        pass

    return ok_any


_GLOBAL_OK = _global_register_all_variants()


def _find_registry_dict(obj: Any) -> Optional[dict]:
    """Return the inner {key: converter} dict from many possible SDK layouts."""
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj
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

        # Register with BOTH integer and string keys so encoder lookups never miss
        fan_conv = HaierHoodFanSpeedConverter()
        light_conv = HaierHoodLightLevelConverter()

        for reg, conv, int_code, str_code in [
            (dec_reg, fan_conv, ERD_HAIER_HOOD_FAN_SPEED_INT, ERD_HAIER_HOOD_FAN_SPEED_STR),
            (enc_reg, fan_conv, ERD_HAIER_HOOD_FAN_SPEED_INT, ERD_HAIER_HOOD_FAN_SPEED_STR),
            (dec_reg, light_conv, ERD_HAIER_HOOD_LIGHT_LEVEL_INT, ERD_HAIER_HOOD_LIGHT_LEVEL_STR),
            (enc_reg, light_conv, ERD_HAIER_HOOD_LIGHT_LEVEL_INT, ERD_HAIER_HOOD_LIGHT_LEVEL_STR),
        ]:
            _register_into_mapping(reg, [int_code, str_code, str_code.lower()], conv)

        _LOGGER.debug("GE Home: Patched appliance-level ERD handlers for Haier hood")

    except Exception:
        _LOGGER.exception("GE Home: Failed to attach Haier hood handlers to appliance")
