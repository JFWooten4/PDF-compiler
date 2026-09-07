from io import BytesIO
import unittest

from app import app
from pdf_compiler import extract_body, HeadingNotFoundError


class StartHeadingTests(unittest.TestCase):
    def test_heading_text_or_markdown_heading_excludes_preamble(self):
        markdown = "Preamble\n\n# Letter\n\nDear Commission,\n"
        for heading in ("Letter", "# Letter", "  # Letter  "):
            with self.subTest(heading=heading):
                self.assertEqual(extract_body(markdown, heading), "Dear Commission,")

    def test_heading_must_not_match_text_on_next_line(self):
        with self.assertRaises(HeadingNotFoundError):
            extract_body("#\nLetter\nBody", "Letter")

    def test_render_uploaded_document_with_markdown_heading(self):
        with app.test_client() as client:
            response = client.post('/render', data={
                'source': (BytesIO(b'Preamble\n# Letter\nDear Commission,'), 'comment.md'),
                'start_heading': '# Letter',
            })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/pdf')
        self.assertTrue(response.data.startswith(b'%PDF-'))

    def test_missing_heading_returns_actionable_client_error(self):
        with app.test_client() as client:
            response = client.post('/render', data={
                'markdown': '# Letter\nDear Commission,',
                'start_heading': 'Missing',
            })
        self.assertEqual(response.status_code, 400)
        self.assertIn("Could not find heading: 'Missing'", response.json['error'])
        self.assertIn('leave Start after heading blank', response.json['error'])


if __name__ == '__main__':
    unittest.main()
