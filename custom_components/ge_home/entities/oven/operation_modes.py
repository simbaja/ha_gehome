"""Helpers for ordering oven operation modes."""

from __future__ import annotations


def order_operation_modes(
    operation_modes: list[str], preferred_mode: str | None, off_mode: str
) -> list[str]:
    """Keep Off first and optionally move a supported preferred mode next.

    When no preference is configured, preserve the supplied ordering exactly.
    """
    ordered_modes = list(operation_modes)
    if preferred_mode in ordered_modes:
        ordered_modes.remove(preferred_mode)
        ordered_modes.insert(0, preferred_mode)
    return [off_mode, *ordered_modes]
