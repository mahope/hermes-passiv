#!/usr/bin/env python3
import unittest
from email.message import Message

from check_live_sitemaps import encoded_url, has_noindex_header


class LiveSitemapTests(unittest.TestCase):
    def test_unicode_path_is_percent_encoded(self) -> None:
        self.assertEqual(
            "https://cleancopy.tools/da/blog/inds%C3%A6t-i-obsidian-ren-markdown",
            encoded_url("https://cleancopy.tools/da/blog/indsæt-i-obsidian-ren-markdown"),
        )

    def test_existing_query_and_fragment_are_safe(self) -> None:
        self.assertEqual(
            "https://mahope.tools/da/?q=%C3%A6",
            encoded_url("https://mahope.tools/da/?q=æ#ignored"),
        )

    def test_x_robots_noindex_is_rejected(self) -> None:
        headers = Message()
        headers["X-Robots-Tag"] = "index, follow"
        self.assertFalse(has_noindex_header(headers))
        headers.replace_header("X-Robots-Tag", "noindex, follow")
        self.assertTrue(has_noindex_header(headers))


if __name__ == "__main__":
    unittest.main()
