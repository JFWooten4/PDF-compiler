from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from reportlab.pdfgen.canvas import Canvas

from configured_renderer import ConfiguredPdfRenderer, LetterSettings, format_page_number


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

    def test_both_headers_render_link_labels_and_pdf_uri_annotations(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "letter.md"
            source.write_text("Body text", encoding="utf-8")
            renderer = ConfiguredPdfRenderer(
                source, root / "letter.pdf", smart_quotes=True,
                settings=LetterSettings(
                    show_date=False,
                    first_page_header='[First & **bold**](https://example.com/first?a=1&b=2)',
                    remaining_page_header="[Later](https://example.com/later?q='value') / [Other](https://example.org)",
                ),
            )
            payload = BytesIO()
            canvas = Canvas(payload, pageCompression=0)
            doc = renderer.document(root / "letter.pdf")
            renderer.draw_branding(canvas, doc)
            canvas.showPage()
            renderer.draw_remaining_header(canvas, doc)
            canvas.save()
            pdf = payload.getvalue()
            self.assertIn(b'/URI (https://example.com/first?a=1&b=2)', pdf)
            self.assertIn(b"/URI (https://example.com/later?q='value')", pdf)
            self.assertIn(b'/URI (https://example.org)', pdf)
            for label in (b'First & ', b'bold', b'Later', b'Other'):
                self.assertIn(label, pdf)
            self.assertNotIn(b'[First', pdf)

    def test_long_linked_header_fits_and_plain_text_is_escaped(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "letter.md"
            source.write_text("Body text", encoding="utf-8")
            renderer = ConfiguredPdfRenderer(
                source, root / "letter.pdf",
                settings=LetterSettings(
                    first_page_header='A & B <review> ' + '[Long header text](https://example.com) ' * 30,
                ),
            )
            renderer.build()
            self.assertTrue(renderer.output.read_bytes().startswith(b'%PDF-'))


if __name__ == "__main__":
    unittest.main()
