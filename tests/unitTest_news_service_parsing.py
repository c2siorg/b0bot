"""Unit tests for NewsService.toJSON defensive parsing behavior."""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch


# Get the current file path
current_file_path = os.path.abspath(__file__)

# Get the grandparent directory
src_directory = os.path.dirname(os.path.dirname(current_file_path))

# Add the parent directory to sys.path
sys.path.append(src_directory)

from services.NewsService import NewsService


class NewsServiceParsingTestCase(unittest.TestCase):
    """Tests for hardening logic in NewsService.toJSON."""

    def setUp(self) -> None:
        """Patch heavy dependencies so parser tests remain fast and isolated."""
        self.db_patcher = patch("services.NewsService.CybernewsDB", return_value=MagicMock())
        self.db_patcher.start()

        self.service = NewsService(model_name=None)

    def tearDown(self) -> None:
        """Stop active dependency patches after each test."""
        self.db_patcher.stop()

    def test_to_json_with_none(self) -> None:
        """Return an empty list when parser input is None."""
        result = self.service.toJSON(None)
        self.assertEqual(result, [])

    def test_to_json_with_empty_string(self) -> None:
        """Return an empty list when parser input is an empty string."""
        result = self.service.toJSON("")
        self.assertEqual(result, [])

    def test_to_json_with_whitespace(self) -> None:
        """Return an empty list when parser input only contains whitespace."""
        result = self.service.toJSON("   \n\t  ")
        self.assertEqual(result, [])

    def test_to_json_with_malformed_line_does_not_crash(self) -> None:
        """Gracefully parse malformed lines without raising index-related errors."""
        malformed = "Intro line\n[headline only]\n"
        result = self.service.toJSON(malformed)
        self.assertIsInstance(result, list)

    def test_to_json_with_single_valid_item(self) -> None:
        """Keep a single valid parsed item instead of dropping the last item."""
        single_item = "Intro line\n[title: first, source one, 01/01/2026, https://example.com/1]\n"
        result = self.service.toJSON(single_item)
        self.assertEqual(len(result), 1)
        self.assertIn("title", result[0])


if __name__ == "__main__":
    unittest.main()
