"""
SDK-agnostic registration for Haier hood ERD encoders/decoders.

Works with:
- Newer SDKs exposing gehomesdk.erd.erd_value_registry
- Older SDKs with per-appliance encoder/decoder registries
- Worst case: a safe monkey-patch on GeAppliance.encode_erd_value
"""
from __future__ import annotations

import inspect
import logging
from typing import Any, Optional, Tuple

from gehomesdk.ge_appliance import GeAppliance

from .haier_hood_codes import (
    ERD_HAIER_HOOD_FAN_SPEED,
    ERD_HAIER_HOOD_LIGHT_ON,
)
from .haier_hood_converters import (
    HaierHoodFanSpeedConverter,
    HaierHoodLightStateConverter,
)

_LOGGER = logging.getLogger(__name__)

_FAN_CODE_STR = "0x5B13"
_LIGHT_CODE_STR = "0x5B17"

_FAN_CONV = HaierHoodFanSpeedConverter()
_LIGHT_CONV = HaierHoodLightStateConverter()


def _to_all_keys(code_like: Any) -> Tuple[Any, ...]:
    """Return a tuple containing both the plain string and an ErdCode instance (if available)."""
    keys = {str(code_like)}
    try:
        from gehomesdk.erd import ErdCode  # type: ignore

        try:
            keys.add(ErdCode(str(code_like)))
        except Exception:
            pass
    except Exception:
        pass
    return tuple(keys)


def _try_global_register() -> bool:
    """Try the modern, global registry API if present."""
    # Newer SDKs: dedicated helpers
    try:
        from gehomesdk.erd.erd_value_registry import (  # type: ignore
            register_erd_encoder,
            register_erd_decoder,
        )

        for k in _to_all_keys(ERD_HAIER_HOOD_FAN_SPEED):
            register_erd_decoder(k, _FAN_CONV)
            register_erd_encoder(k, _FAN_CONV)
        for k in _to_all_keys(ERD_HAIER_HOOD_LIGHT_ON):
            register_erd_decoder(k, _LIGHT_CONV)
            register_erd_encoder(k, _LIGHT_CONV)

        _LOGGER.debug("GE Home: Registered Haier hood ERDs via global registry API")
        return True
    except Exception as ex:
        _LOGGER.debug("GE Home: No global ERD registry API (%s). Will patch per-appliance.", ex)

    # Some builds expose a module-level dict
    try:
        from gehomesdk.erd import erd_value_registry as _mod  # type: ignore

        reg = getattr(_mod, "REGISTRY", None) or getattr(_mod, "_REGISTRY", None)
        if isinstance(reg, dict):
            for k in _to_all_keys(ERD_HAIER_HOOD_FAN_SPEED):
                reg.setdefault("decoder", {})[k] = _FAN_CONV
                reg.setdefault("encoder", {})[k] = _FAN_CONV
            for k in _to_all_keys(ERD_HAIER_HOOD_LIGHT_ON):
                reg.setdefault("decoder", {})[k] = _LIGHT_CONV
                reg.setdefault("encoder", {})[k] = _LIGHT_CONV
            _LOGGER.debug("GE Home: Registered Haier hood ERDs via legacy global dict")
            return True
    except Exception:
        pass

    return False


_GLOBAL_OK = _try_global_register()


def _find_registry_dict(obj: Any) -> Optional[dict]:
    """Return the inner {ErdCode|str: converter} dict from many possible SDK layouts."""
    if obj is None:
        return None

    if isinstance(obj, dict):
        return obj

    # common attribute spellings
    for attr in (
        "_registry",
        "registry",
        "_erd_encoder_registry",
        "_erd_decoder_registry",
        "converters",
        "converter_map",
        "_converters",
    ):
        reg = getattr(obj, attr, None)
        if isinstance(reg, dict):
            return reg

    return None


def _get_encoder_decoder_regs(appliance: GeAppliance) -> tuple[Optional[dict], Optional[dict]]:
    """Probe multiple SDK layouts to find encoder/decoder registry dicts."""
    enc_candidates = [
        getattr(appliance, name, None)
        for name in ("_encoder", "_erd_encoder", "encoder", "erd_encoder", "value_encoder")
    ]
    dec_candidates = [
        getattr(appliance, name, None)
        for name in ("_decoder", "_erd_decoder", "decoder", "erd_decoder", "value_decoder")
    ]

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


def _register_in_dict(reg: dict, code_like: Any, conv: Any) -> None:
    for k in _to_all_keys(code_like):
        reg[k] = conv
        # also be sure a plain uppercase string works (some SDKs normalize)
        reg[str(k).upper()] = conv  # type: ignore


def _install_encode_fallback() -> None:
    """Last resort: patch GeAppliance.encode_erd_value to encode our two ERDs."""
    if getattr(GeAppliance, "_haier_hood_encode_patch", False):
        return

    orig = GeAppliance.encode_erd_value  # type: ignore[attr-defined]

    def patched(self: GeAppliance, erd_code: Any, value: Any):  # type: ignore[no-redef]
        code_str = str(erd_code).upper()
        try:
            if code_str == _FAN_CODE_STR.upper():
                return _FAN_CONV.erd_encode(value)
            if code_str == _LIGHT_CODE_STR.upper():
                return _LIGHT_CONV.erd_encode(value)
        except Exception as ex:
            _LOGGER.warning("GE Home: Haier hood fallback encode failed for %s: %s", code_str, ex)

        return orig(self, erd_code, value)

    GeAppliance.encode_erd_value = patched  # type: ignore[assignment]
    GeAppliance._haier_hood_encode_patch = True  # type: ignore[attr-defined]
    _LOGGER.debug("GE Home: Installed Haier hood encode fallback")


def ensure_haier_hood_handlers_for_appliance(appliance: GeAppliance) -> None:
    """
    If the SDK doesn't have a global registry, attach our handlers directly to this appliance's
    encoder/decoder registries. Safe to call multiple times.
    """
    if _GLOBAL_OK:
        return  # already globally handled

    try:
        enc_reg, dec_reg = _get_encoder_decoder_regs(appliance)

        if enc_reg and dec_reg:
            _register_in_dict(dec_reg, ERD_HAIER_HOOD_FAN_SPEED, _FAN_CONV)
            _register_in_dict(enc_reg, ERD_HAIER_HOOD_FAN_SPEED, _FAN_CONV)

            _register_in_dict(dec_reg, ERD_HAIER_HOOD_LIGHT_ON, _LIGHT_CONV)
            _register_in_dict(enc_reg, ERD_HAIER_HOOD_LIGHT_ON, _LIGHT_CONV)

            _LOGGER.debug("GE Home: Patched appliance-level ERD handlers for Haier hood")
            return

        # If we couldn't find registries on this SDK, ensure the write path still works.
        _install_encode_fallback()

    except Exception:
        _LOGGER.exception("GE Home: Failed to attach Haier hood handlers to appliance; using fallback")
        _install_encode_fallback()
