from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from PIL import Image

from configured_renderer import ConfiguredPdfRenderer, LetterSettings, format_header_date


class ConfiguredRendererTests(unittest.TestCase):
    def test_date_presets(self):
        today = date(2026, 9, 6)
        self.assertEqual(format_header_date(LetterSettings(), today=today), "September 6, 2026")
        self.assertEqual(
            format_header_date(LetterSettings(date_format="day_month_year"), today=today),
            "6 September 2026",
        )
        self.assertEqual(
            format_header_date(LetterSettings(date_format="iso"), today=today),
            "2026-09-06",
        )
        self.assertEqual(
            format_header_date(LetterSettings(date_format="us_numeric"), today=today),
            "09/06/2026",
        )

    def test_trim_logo_padding(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.md"
            source.write_text("## Body\n\nText", encoding="utf-8")
            logo = root / "logo.png"
            image = Image.new("RGBA", (200, 100), "white")
            image.paste((0, 0, 0, 255), (60, 30, 140, 70))
            image.save(logo)

            renderer = ConfiguredPdfRenderer(
                source,
                root / "output.pdf",
                logo=logo,
                settings=LetterSettings(logo_treatment="trim"),
            )
            prepared = renderer._prepared_logo()
            self.assertIsNotNone(prepared)
            self.assertEqual(prepared[1:3], (80, 40))

    def test_addressee_box_is_optional(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.md"
            source.write_text("## Body\n\nText", encoding="utf-8")
            renderer = ConfiguredPdfRenderer(
                source,
                root / "output.pdf",
                settings=LetterSettings(addressee="Jane Doe\nAgency", addressee_box=False),
            )
            self.assertEqual(len(renderer._addressee_block()), 2)


if __name__ == "__main__":
    unittest.main()
