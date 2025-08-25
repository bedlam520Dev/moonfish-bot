# Copyright © 2025 BEDLAM520 Development
# -*- coding: utf-8 -*-

"""Unit tests for _load_keywords_file function in main.py.

Tests both valid and invalid file loading scenarios.

"""

import unittest
from pathlib import Path
from main import _load_keywords_file, DEFAULT_KEYWORDS

class TestLoadKeywordsFile(unittest.TestCase):
    def test_valid_file(self):
        """Test loading a valid keywords.json file."""
        result = _load_keywords_file(Path("keywords.json"))
        self.assertIsInstance(result, dict)
        self.assertTrue("moon" in result)

    def test_invalid_file(self):
        """Test loading an invalid/nonexistent file falls back to defaults."""
        result = _load_keywords_file(Path("nonexistent.json"))
        self.assertEqual(result, DEFAULT_KEYWORDS)

if __name__ == "__main__":
    unittest.main()
