# Copyright © 2025 BEDLAM520 Development
# -*- coding: utf-8 -*-

"""Unit tests for chat_probs function in main.py.

Tests default probability values for a chat.

"""

import unittest
from main import chat_probs

class TestChatProbs(unittest.TestCase):
    def test_chat_probs_default(self):
        """Test that chat_probs returns default values for a new chat_id."""
        chat_id = 12345
        k, m, g = chat_probs(chat_id)
        self.assertIsInstance(k, (int, float))
        self.assertIsInstance(m, (int, float))
        self.assertIsInstance(g, (int, float))

if __name__ == "__main__":
    unittest.main()
