"""Tests for oven operation mode preference ordering."""

import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = (
    Path(__file__).parents[1]
    / "custom_components/ge_home/entities/oven/operation_modes.py"
)
SPEC = importlib.util.spec_from_file_location("oven_operation_modes", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
order_operation_modes = MODULE.order_operation_modes


class TestOrderOperationModes(unittest.TestCase):
    def setUp(self):
        self.modes = ["Convection Roast", "Conv. Multi-Bake", "Bake"]

    def test_keeps_existing_order_without_preference(self):
        self.assertEqual(
            ["off", *self.modes],
            order_operation_modes(self.modes, None, "off"),
        )

    def test_moves_supported_preference_to_front(self):
        self.assertEqual(
            ["off", "Bake", "Convection Roast", "Conv. Multi-Bake"],
            order_operation_modes(self.modes, "Bake", "off"),
        )

    def test_off_remains_first(self):
        self.assertEqual("off", order_operation_modes(self.modes, "Bake", "off")[0])

    def test_preserves_all_other_modes_and_their_order(self):
        result = order_operation_modes(self.modes, "Bake", "off")
        self.assertCountEqual(["off", *self.modes], result)
        self.assertEqual(["Convection Roast", "Conv. Multi-Bake"], result[2:])

    def test_unsupported_preference_falls_back_to_existing_order(self):
        self.assertEqual(
            ["off", *self.modes],
            order_operation_modes(self.modes, "Air Fry", "off"),
        )


if __name__ == "__main__":
    unittest.main()
