"""
SDK-agnostic registration for Haier hood ERD encoders/decoders.

Works with:
- Newer SDKs exposing gehomesdk.erd.erd_value_registry
- Older SDKs that hang encoder/decoder registries off the appliance or modules
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from gehomesdk.ge_appliance import GeAppliance

from .haier_hood_codes import (
    ERD_HAIER_HOOD_FAN_SPEED,
    ERD_HAIER_HOOD_LIGHT_LEVEL,  # alias -> 0x5B17
)
from .haier_hood_converters import (
    HaierHoodFanSpeedConverter,
    HaierHoodLightLevelConverter,
)

_LOGGER = logging.getLogger(__name__)


#  helpers 
def _register_both_key_types(reg: dict, hex_code: str, converter: Any) -> None:
    """Register under both the string key and ErdCode(..) key if available."""
    # Always string
    if hex_code not in reg:
        reg[hex_code] = converter
    # ErdCode variant (if SDK exposes ErdCode)
    try:
        from gehomesdk.erd import ErdCode  # type: ignore

        ec = ErdCode(hex_code)
        if ec not in reg:
            reg[ec] = converter
    except Exception:
        pass


def _try_global_register() -> bool:
    """Try the modern, global registry API if present."""
    try:
        # New-ish names in the SDK (function-style helpers)
        from gehomesdk.erd.erd_value_registry import (  # type: ignore
            register_erd_encoder,
            register_erd_decoder,
        )

        # Register with both key types to be safe
        for hex_code, conv in (
            ("0x5B13", HaierHoodFanSpeedConverter()),
            ("0x5B17", HaierHoodLightLevelConverter()),
        ):
            try:
                # string key
                register_erd_decoder(hex_code, conv)
                register_erd_encoder(hex_code, conv)
            except Exception:
                pass
            try:
                from gehomesdk.erd import ErdCode  # type: ignore

                register_erd_decoder(ErdCode(hex_code), conv)
                register_erd_encoder(ErdCode(hex_code), conv)
            except Exception:
                pass

        _LOGGER.debug("GE Home: Registered Haier hood ERDs via global registry API")
        return True
    except Exception as ex:
        _LOGGER.debug(
            "GE Home: No global ERD registry API (%s). Will patch per-appliance.", ex
        )
        return False


_GLOBAL_OK = _try_global_register()


def _maybe_dict(obj: Any) -> Optional[dict]:
    """Return a dict if obj looks like a registry or contains one."""
    if obj is None:
        return None

    # Direct dict
    if isinstance(obj, dict):
        return obj

    # Common attribute spellings on instances/modules/wrappers
    for attr in ("_registry", "registry", "_erd_encoder_registry", "_erd_decoder_registry"):
        reg = getattr(obj, attr, None)
        if isinstance(reg, dict):
            return reg
        # nested object holding the dict (eg. registry._registry)
        if reg is not None:
            for inner in ("_registry", "registry", "map", "_map", "values", "_values"):
                inner_val = getattr(reg, inner, None)
                if isinstance(inner_val, dict):
                    return inner_val

    return None


def _get_encoder_decoder_regs(appliance: GeAppliance) -> tuple[Optional[dict], Optional[dict]]:
    """Probe multiple SDK layouts to find encoder/decoder registry dicts."""
    enc_candidates = [
        getattr(appliance, name, None) for name in ("_encoder", "_erd_encoder", "encoder")
    ]
    dec_candidates = [
        getattr(appliance, name, None) for name in ("_decoder", "_erd_decoder", "decoder")
    ]

    # Also try the modules directly (older SDKs sometimes stash here)
    try:
        import gehomesdk.erd.erd_encoder as enc_mod  # type: ignore
        enc_candidates.append(enc_mod)
    except Exception:
        pass
    try:
        import gehomesdk.erd.erd_decoder as dec_mod  # type: ignore
        dec_candidates.append(dec_mod)
    except Exception:
        pass

    enc_reg = None
    dec_reg = None

    for cand in enc_candidates:
        enc_reg = _maybe_dict(cand) or _maybe_dict(getattr(cand, "_registry", None))
        if enc_reg:
            break

    for cand in dec_candidates:
        dec_reg = _maybe_dict(cand) or _maybe_dict(getattr(cand, "_registry", None))
        if dec_reg:
            break

    if not enc_reg or not dec_reg:
        _LOGGER.debug(
            "GE Home: encoder candidate types=%s; decoder candidate types=%s",
            [type(c).__name__ for c in enc_candidates if c is not None],
            [type(c).__name__ for c in dec_candidates if c is not None],
        )
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

        # Register both string and ErdCode keys (SDK differences)
        _register_both_key_types(dec_reg, "0x5B13", HaierHoodFanSpeedConverter())
        _register_both_key_types(enc_reg, "0x5B13", HaierHoodFanSpeedConverter())

        _register_both_key_types(dec_reg, "0x5B17", HaierHoodLightLevelConverter())
        _register_both_key_types(enc_reg, "0x5B17", HaierHoodLightLevelConverter())

        _LOGGER.debug("GE Home: Patched appliance-level ERD handlers for Haier hood")
    except Exception:
        _LOGGER.exception("GE Home: Failed to attach Haier hood handlers to appliance")
