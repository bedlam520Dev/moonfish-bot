# Copyright © 2025 BEDLAM520 Development
# -*- coding: utf-8 -*-

"""Unit tests for should_reply function in main.py.

Tests reply logic for always true and always false probabilities.

"""

import unittest
from main import should_reply

class TestShouldReply(unittest.TestCase):
    def test_should_reply_always_true(self):
        """Test should_reply returns True when probability is 100."""
        self.assertTrue(all(should_reply(100) for _ in range(100)))

    def test_should_reply_always_false(self):
        """Test should_reply returns False when probability is 0."""
        self.assertTrue(all(not should_reply(0) for _ in range(100)))

if __name__ == "__main__":
    unittest.main()
