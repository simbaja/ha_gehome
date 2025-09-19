"""Compatibility helpers for registering ERD value converters across SDK versions."""
from __future__ import annotations
import logging
from typing import Any

_LOGGER = logging.getLogger(__name__)

def try_register_globally(fan_erd: Any, light_erd: Any, fan_conv: Any, light_conv: Any) -> bool:
    """
    Try to register converters with the SDK's global ERD registry.
    Returns True if successful, False otherwise (older SDKs).
    """
    try:
        # Newer SDKs (object-style registry)
        try:
            from gehomesdk.erd.erd_value_registry import ERD_VALUE_REGISTRY as _REG  # type: ignore
            if hasattr(_REG, "register"):
                _REG.register(fan_erd, fan_conv)
                _REG.register(light_erd, light_conv)
                return True
        except Exception:
            # Older SDKs (class-style API or function)
            from gehomesdk.erd.erd_value_registry import ErdValueRegistry as _REG  # type: ignore
            if hasattr(_REG, "register"):
                _REG.register(fan_erd, fan_conv)
                _REG.register(light_erd, light_conv)
                return True
            # Very old: function-style
            try:
                from gehomesdk.erd.erd_value_registry import register as _register  # type: ignore
                _register(fan_erd, fan_conv)
                _register(light_erd, light_conv)
                return True
            except Exception:
                pass
    except Exception as e:
        _LOGGER.debug("Global ERD registry not available: %s", e)

    return False


def ensure_converters_on_appliance(appliance, fan_erd: Any, light_erd: Any, fan_conv: Any, light_conv: Any) -> None:
    """
    Ensure converters exist **at least** on this appliance's encoder registry.
    Safe for all SDK versions.
    """
    try:
        enc = getattr(appliance, "_encoder", None)
        reg = getattr(enc, "_registry", None)
        if isinstance(reg, dict):
            # Only set if missing; keeps idempotent behavior.
            reg.setdefault(fan_erd, fan_conv)
            reg.setdefault(light_erd, light_conv)
        else:
            _LOGGER.debug("Appliance encoder registry unavailable; converters not injected.")
    except Exception as e:
        _LOGGER.debug("Failed to inject converters on appliance: %s", e)
