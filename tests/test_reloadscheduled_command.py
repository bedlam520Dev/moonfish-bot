# Copyright © 2025 BEDLAM520 Development
# -*- coding: utf-8 -*-

"""Unit tests for /reloadscheduled command in MoonFishHypeBot.

Tests both successful and failed reload scenarios.

"""

import unittest
from unittest.mock import MagicMock, patch
from main import reloadscheduled_command, SCHEDULED_HYPE

class TestReloadScheduledCommand(unittest.IsolatedAsyncioTestCase):
    @patch("main._load_scheduled_hype_file")
    async def test_reloadscheduled_success(self, mock_load):
        """Test successful reload of scheduled hype messages."""
        mock_load.return_value = {"gm": ["a"], "noon": ["b"], "gn": ["c"]}
        update = MagicMock()
        context = MagicMock()
        message = MagicMock()
        update.message = message
        await reloadscheduled_command(update, context)
        message.reply_text.assert_called_with("Reloaded scheduled hype messages: gm=1, noon=1, gn=1")

    @patch("main._load_scheduled_hype_file", side_effect=Exception("fail"))
    async def test_reloadscheduled_failure(self, mock_load):
        """Test failure to reload scheduled hype messages."""
        update = MagicMock()
        context = MagicMock()
        message = MagicMock()
        update.message = message
        await reloadscheduled_command(update, context)
        self.assertTrue(message.reply_text.call_args[0][0].startswith("Failed to reload scheduled hype messages:"))

if __name__ == "__main__":
    unittest.main()
