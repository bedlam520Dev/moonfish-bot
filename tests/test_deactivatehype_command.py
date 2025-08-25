# Copyright © 2025 BEDLAM520 Development
# -*- coding: utf-8 -*-

"""Unit tests for /deactivatehype command in MoonFishHypeBot.

Tests deactivation logic for scheduled hype per chat.

"""

import unittest
from unittest.mock import MagicMock
from main import deactivatehype_command, scheduled_hype_active

class TestDeactivateHypeCommand(unittest.IsolatedAsyncioTestCase):
    async def test_deactivatehype_sets_inactive(self):
        """Test that /deactivatehype sets scheduled hype inactive for the chat. """
        update = MagicMock()
        context = MagicMock()
        chat = MagicMock()
        message = MagicMock()
        chat.id = 12345
        update.effective_chat = chat
        update.message = message
        scheduled_hype_active[chat.id] = True
        await deactivatehype_command(update, context)
        self.assertFalse(scheduled_hype_active[chat.id])
        message.reply_text.assert_called_with("Scheduled hype messages deactivated for this chat.")

if __name__ == "__main__":
    unittest.main()
