# Copyright © 2025 BEDLAM520 Development
# -*- coding: utf-8 -*-

"""Unit tests for core functions in main.py.

Tests file loading, probability logic, and reply selection.

"""

import unittest
import json
from pathlib import Path
from main import (
    _load_keywords_file,
    _load_idle_file,
    _load_general_file,
    chat_probs,
    should_reply,
    DEFAULT_KEYWORDS,
    DEFAULT_IDLE,
    DEFAULT_GENERAL,
)

class TestMoonFishBot(unittest.TestCase):
    def setUp(self):
        self.keywords_path = Path("keywords.json")
        self.idle_path = Path("idle_messages.json")
        self.general_path = Path("general_replies.json")

    def test_load_keywords_file_valid(self):
        result = _load_keywords_file(self.keywords_path)
        self.assertIsInstance(result, dict)
        self.assertTrue("moon" in result)

    def test_load_keywords_file_invalid(self):
        result = _load_keywords_file(Path("nonexistent.json"))
        self.assertEqual(result, DEFAULT_KEYWORDS)

    def test_load_idle_file_valid(self):
        result = _load_idle_file(self.idle_path)
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)

    def test_load_idle_file_invalid(self):
        result = _load_idle_file(Path("nonexistent.json"))
        self.assertEqual(result, DEFAULT_IDLE)

    def test_load_general_file_valid(self):
        result = _load_general_file(self.general_path)
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)

    def test_load_general_file_invalid(self):
        result = _load_general_file(Path("nonexistent.json"))
        self.assertEqual(result, DEFAULT_GENERAL)

    def test_chat_probs(self):
        # Simulate overrides
        chat_id = 12345
        # Should return defaults if no override
        k, m, g = chat_probs(chat_id)
        self.assertIsInstance(k, (int, float))
        self.assertIsInstance(m, (int, float))
        self.assertIsInstance(g, (int, float))

    def test_should_reply(self):
        # Should return True sometimes, False sometimes
        true_count = sum(should_reply(100) for _ in range(100))
        false_count = sum(should_reply(0) for _ in range(100))
        self.assertEqual(true_count, 100)
        self.assertEqual(false_count, 0)

if __name__ == "__main__":
    unittest.main()
