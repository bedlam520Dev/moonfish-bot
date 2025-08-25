# Copyright © 2025 BEDLAM520 Development
# -*- coding: utf-8 -*-

"""Unit tests for scheduled hype message loading in MoonFishHypeBot.

Tests valid, missing, invalid, and partial file scenarios.

"""

import unittest
from pathlib import Path
from main import _load_scheduled_hype_file, DEFAULT_SCHEDULED_HYPE

class TestLoadScheduledHypeFile(unittest.TestCase):
    def test_valid_file(self):
        # Create a temporary valid file
        path = Path("test_scheduled_hype_valid.json")
        data = {"gm": ["msg1"], "noon": ["msg2"], "gn": ["msg3"]}
        path.write_text(str(data).replace("'", '"'))
        result = _load_scheduled_hype_file(path)
        self.assertEqual(result["gm"], ["msg1"])
        self.assertEqual(result["noon"], ["msg2"])
        self.assertEqual(result["gn"], ["msg3"])
        path.unlink()

    def test_missing_file(self):
        path = Path("nonexistent.json")
        result = _load_scheduled_hype_file(path)
        self.assertEqual(result, {"gm": [], "noon": [], "gn": []})

    def test_invalid_file(self):
        path = Path("test_scheduled_hype_invalid.json")
        path.write_text("not a json")
        result = _load_scheduled_hype_file(path)
        self.assertEqual(result, {"gm": [], "noon": [], "gn": []})
        path.unlink()

    def test_default_fallback(self):
        # Simulate missing keys
        path = Path("test_scheduled_hype_partial.json")
        data = {"gm": ["msg1"]}
        path.write_text(str(data).replace("'", '"'))
        result = _load_scheduled_hype_file(path)
        self.assertEqual(result["gm"], ["msg1"])
        self.assertEqual(result["noon"], [])
        self.assertEqual(result["gn"], [])
        path.unlink()

if __name__ == "__main__":
    unittest.main()
