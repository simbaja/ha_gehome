"""
SDK-agnostic registration for Haier hood ERD encoders/decoders.
Works with:
- Newer SDKs exposing gehomesdk.erd.erd_value_registry
- Older SDKs where encoder/decoder registries are hanging off the appliance
- Registries implemented as dicts OR custom "registry" objects
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from gehomesdk.ge_appliance import GeAppliance

from .haier_hood_codes import (
    ERD_HAIER_HOOD_FAN_COMMAND,
    ERD_HAIER_HOOD_FAN_STATUS,
    ERD_HAIER_HOOD_LIGHT_COMMAND,
    ERD_HAIER_HOOD_LIGHT_STATUS,
)
from .haier_hood_converters import (
    HaierHoodFanSpeedConverter,
    HaierHoodLightLevelConverter,
)

_LOGGER = logging.getLogger(__name__)


# Registration helpers that work across SDK variants

def _erd_hex(code: Any) -> str:
    """Return the hex string form for the ERD code constant."""
    # Our constants may already be strings or ErdCode('0x....').
    try:
        s = str(code)
        return s if s.startswith("0x") else s
    except Exception:
        return "0x????"


def _register_in_target(target: Any, key: Any, conv: Any) -> bool:
    """
    Try many ways to add (key -> conv) into a registry-like object.
    Supports:
    - Mapping semantics via __setitem__
    - Methods: register(key, conv), add(key, conv), set(key, conv)
    - Nested dict objects under common attribute names
    """
    if target is None:
        return False

    # 1) Mapping-style setitem
    try:
        target[key] = conv  # type: ignore[index]
        return True
    except Exception:
        pass

    # 2) Common method names
    for meth in ("register", "add", "set", "set_item"):
        fn = getattr(target, meth, None)
        if callable(fn):
            try:
                fn(key, conv)
                return True
            except Exception:
                continue

    # 3) Try well-known inner attributes that may hold the dict/map
    for attr in ("_registry", "registry", "map", "_map", "values", "_values", "_dict"):
        inner = getattr(target, attr, None)
        if inner is not None and _register_in_target(inner, key, conv):
            return True

    return False


def _register_both_key_types(target: Any, hex_code: str, conv: Any) -> bool:
    """Register converter with both string and ErdCode keys (if ErdCode exists)."""
    ok = False
    # string key
    ok = _register_in_target(target, hex_code, conv) or ok

    # ErdCode key (if available)
    try:
        from gehomesdk.erd import ErdCode  # type: ignore
        ok = _register_in_target(target, ErdCode(hex_code), conv) or ok
    except Exception:
        pass

    return ok


def _try_global_register() -> bool:
    """Try modern global registry APIs if present in the SDK."""
    try:
        from gehomesdk.erd.erd_value_registry import (  # type: ignore
            register_erd_encoder,
            register_erd_decoder,
        )

        for hex_code, conv in (
            ("0x5B13", HaierHoodFanSpeedConverter()),
            ("0x5B17", HaierHoodLightLevelConverter()),
            ("0x5B15", HaierHoodFanSpeedConverter()),
            ("0x5B16", HaierHoodLightLevelConverter()),
        ):
            # String key
            try:
                register_erd_decoder(hex_code, conv)
                register_erd_encoder(hex_code, conv)
            except Exception:
                pass
            # ErdCode key
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


def _maybe_registry(obj: Any) -> Optional[Any]:
    """Return a registry-like object (dict or custom) if present."""
    if obj is None:
        return None

    # Direct dict/registry object
    if isinstance(obj, dict):
        return obj

    # Common attribute spellings and nested containers
    for attr in ("_registry", "registry", "_erd_encoder_registry", "_erd_decoder_registry"):
        reg = getattr(obj, attr, None)
        if reg is None:
            continue
        if isinstance(reg, dict):
            return reg
        # Might be a custom registry object; accept it and let _register_in_target handle it
        # Also check for nested dict within it.
        for inner in (None, "_registry", "registry", "map", "_map", "values", "_values"):
            candidate = getattr(reg, inner, reg) if inner else reg
            if isinstance(candidate, dict):
                return candidate
        return reg

    return None


def _get_encoder_decoder_regs(appliance: GeAppliance) -> tuple[Optional[Any], Optional[Any]]:
    """Probe multiple SDK layouts to find encoder/decoder registries (or registry-like objects)."""
    enc_candidates = [getattr(appliance, name, None) for name in ("_encoder", "_erd_encoder", "encoder")]
    dec_candidates = [getattr(appliance, name, None) for name in ("_decoder", "_erd_decoder", "decoder")]

    # Also try the modules directly (some SDKs stash globals here)
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
        enc_reg = _maybe_registry(cand) or _maybe_registry(getattr(cand, "_registry", None))
        if enc_reg is not None:
            break

    for cand in dec_candidates:
        dec_reg = _maybe_registry(cand) or _maybe_registry(getattr(cand, "_registry", None))
        if dec_reg is not None:
            break

    if enc_reg is None or dec_reg is None:
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

    IMPORTANT: We will register to whatever we can find. Encoder-only is sufficient for writes.
    """
    if _GLOBAL_OK:
        return  # already globally handled

    try:
        enc_reg, dec_reg = _get_encoder_decoder_regs(appliance)

        registered_any = False

        # Register on ENCODER (needed for set_erd_value)
        if enc_reg is not None:
            registered_any |= _register_both_key_types(enc_reg, "0x5B13", HaierHoodFanSpeedConverter())
            registered_any |= _register_both_key_types(enc_reg, "0x5B17", HaierHoodLightLevelConverter())
            registered_any |= _register_both_key_types(enc_reg, "0x5B15", HaierHoodFanSpeedConverter())
            registered_any |= _register_both_key_types(enc_reg, "0x5B16", HaierHoodLightLevelConverter())

        # Register on DECODER (nice to have)
        if dec_reg is not None:
            registered_any |= _register_both_key_types(dec_reg, "0x5B13", HaierHoodFanSpeedConverter())
            registered_any |= _register_both_key_types(dec_reg, "0x5B17", HaierHoodLightLevelConverter())
            registered_any |= _register_both_key_types(dec_reg, "0x5B15", HaierHoodFanSpeedConverter())
            registered_any |= _register_both_key_types(dec_reg, "0x5B16", HaierHoodLightLevelConverter())

        if not registered_any:
            # Keep the exception (with our debug above) so we can see layouts if it still fails.
            raise RuntimeError("Could not attach Haier hood handlers to any registry")

        _LOGGER.debug("GE Home: Patched ERD handlers for Haier hood (encoder%s decoder%s)",
                      "✔" if enc_reg is not None else "✖",
                      "✔" if dec_reg is not None else "✖")

    except Exception:
        _LOGGER.exception("GE Home: Failed to attach Haier hood handlers to appliance")