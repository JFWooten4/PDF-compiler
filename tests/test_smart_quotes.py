import inspect
import unittest

from pdf_compiler import PdfRenderer, smarten_quotes


class SmartQuotesTests(unittest.TestCase):
    def test_typographic_quotes_and_apostrophes(self):
        self.assertEqual(
            smarten_quotes('"Hello," she said. It\'s fine.'),
            '“Hello,” she said. It’s fine.',
        )

    def test_inline_code_is_unchanged(self):
        self.assertEqual(
            smarten_quotes('`print("x")` and "text"'),
            '`print("x")` and “text”',
        )

    def test_renderer_defaults_to_straight_quotes(self):
        default = inspect.signature(PdfRenderer).parameters["smart_quotes"].default
        self.assertIs(default, False)


if __name__ == "__main__":
    unittest.main()
