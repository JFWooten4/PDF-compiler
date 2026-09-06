import unittest

from configured_renderer import LetterSettings, format_page_number


class HeaderFooterSettingsTests(unittest.TestCase):
    def test_page_number_formats(self):
        self.assertEqual(format_page_number("none", 2, 5), "")
        self.assertEqual(format_page_number("number", 2, 5), "2")
        self.assertEqual(format_page_number("page_number", 2, 5), "Page 2")
        self.assertEqual(format_page_number("number_of_total", 2, 5), "2 of 5")
        self.assertEqual(format_page_number("page_number_of_total", 2, 5), "Page 2 of 5")

    def test_page_numbers_default_off(self):
        self.assertEqual(LetterSettings().page_number_style, "none")

    def test_headers_are_separate_settings(self):
        settings = LetterSettings(
            first_page_header="First-page header",
            remaining_page_header="Running header",
        )
        self.assertEqual(settings.first_page_header, "First-page header")
        self.assertEqual(settings.remaining_page_header, "Running header")

    def test_unknown_page_number_style_is_rejected(self):
        with self.assertRaises(ValueError):
            LetterSettings(page_number_style="roman")


if __name__ == "__main__":
    unittest.main()
