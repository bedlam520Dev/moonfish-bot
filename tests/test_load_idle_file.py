# Copyright © 2025 BEDLAM520 Development
# -*- coding: utf-8 -*-

"""Unit tests for _load_idle_file function in main.py.

Tests both valid and invalid file loading scenarios.

"""

import unittest
from pathlib import Path
from main import _load_idle_file, DEFAULT_IDLE

class TestLoadIdleFile(unittest.TestCase):
    def test_valid_file(self):
        """Test loading a valid idle_messages.json file."""
        result = _load_idle_file(Path("idle_messages.json"))
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)

    def test_invalid_file(self):
        """Test loading an invalid/nonexistent file falls back to defaults."""
        result = _load_idle_file(Path("nonexistent.json"))
        self.assertEqual(result, DEFAULT_IDLE)

if __name__ == "__main__":
    unittest.main()
