import copy
from pathlib import Path
import re
import unittest

import network_notice as notice

SCRIPT = Path(__file__).resolve().parent
DATA = SCRIPT.parent / "content/network-permission-notice.json"
if not DATA.exists():
    DATA = SCRIPT / "network-permission-notice.json"
BASE = '<!doctype html><html><head><title>Original</title></head><body><main><h1>Original</h1><p class="date">2026-10-29</p><section><h2>Existing policy</h2><p>Unchanged.</p></section></main></body></html>'


class NoticeTests(unittest.TestCase):
    def setUp(self):
        self.data = notice.load_notice(DATA)

    def test_localized_updates_preserve_existing_content_and_are_idempotent(self):
        for locale in notice.LOCALES:
            for detailed in (False, True):
                with self.subTest(locale=locale, detailed=detailed):
                    page = notice.inject_notice(BASE, self.data, locale, detailed=detailed)
                    self.assertEqual(page, notice.inject_notice(page, self.data, locale, detailed=detailed))
                    if locale in notice.NOTICE_LOCALES:
                        self.assertEqual(page.count('id="wireless-data-notice"'), 1)
                        self.assertIn(notice.APPLE_DISCUSSION, page)
                        self.assertIn(notice.ISSUE, page)
                    else:
                        self.assertEqual(page, BASE)
                    stripped = re.sub(re.escape(notice.START) + r".*?" + re.escape(notice.END), "", page, flags=re.S)
                    stripped = re.sub(r'<style id="network-notice-style">.*?</style>', "", stripped, flags=re.S)
                    self.assertEqual(BASE, stripped)

    def test_translated_copy_cannot_inject_markup(self):
        data = copy.deepcopy(self.data)
        data["localizations"]["zh-Hans"]["summary"] = '<img src=x onerror="alert(1)"> & text'
        rendered = notice.render_notice(data, "zh-Hans", detailed=False)
        self.assertNotIn("<img", rendered)
        self.assertIn("&lt;img", rendered)
        self.assertIn("&amp; text", rendered)

    def test_home_link_points_to_localized_faq(self):
        page = notice.inject_notice(BASE, self.data, "zh-Hans", detailed=False, index=True)
        self.assertIn('href="zh-Hans/support.html#wireless-data-notice"', page)
        self.assertIn('datetime="2026-11-08"', page)

    def test_unexpected_page_structure_is_rejected(self):
        with self.assertRaises(ValueError):
            notice.inject_notice("<html><head></head><body>Missing heading</body></html>", self.data, "zh-Hans", detailed=True)
        with self.assertRaises(ValueError):
            notice.inject_notice(BASE + notice.START, self.data, "en-US", detailed=True)

    def test_existing_foreign_notices_are_removed_without_touching_page_content(self):
        legacy = copy.deepcopy(self.data)
        legacy["localizations"] = {locale: legacy["localizations"]["zh-Hans"] for locale in notice.LOCALES}
        for locale in notice.LOCALES - notice.NOTICE_LOCALES:
            with self.subTest(locale=locale):
                old = notice.inject_notice(BASE, legacy, locale, detailed=True)
                self.assertIn(notice.START, old)
                self.assertEqual(notice.inject_notice(old, self.data, locale, detailed=True), BASE)
                self.assertEqual(notice.render_notice_markdown(self.data, locale), "")


if __name__ == "__main__":
    unittest.main()
