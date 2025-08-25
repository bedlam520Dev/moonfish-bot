# Copyright © 2025 BEDLAM520 Development
# -*- coding: utf-8 -*-

"""Unit tests for /activatehype command in MoonFishHypeBot.

Tests activation logic for scheduled hype per chat.

"""

Tests activation logic for scheduled hype per chat.
import unittest
from unittest.mock import MagicMock
from main import activatehype_command, scheduled_hype_active

class TestActivateHypeCommand(unittest.IsolatedAsyncioTestCase):
    async def test_activatehype_sets_active(self):
        """Test that /activatehype sets scheduled hype active for the chat. """
        update = MagicMock()
        context = MagicMock()
        chat = MagicMock()
        message = MagicMock()
        chat.id = 12345
        update.effective_chat = chat
        update.message = message
        scheduled_hype_active[chat.id] = False
        await activatehype_command(update, context)
        self.assertTrue(scheduled_hype_active[chat.id])
        message.reply_text.assert_called_with("Scheduled hype messages activated for this chat.")

if __name__ == "__main__":
    unittest.main()
