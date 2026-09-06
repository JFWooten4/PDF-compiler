from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from configured_renderer import (
    ConfiguredPdfRenderer,
    LetterSettings,
    format_section_number,
)


class SectionAndTocTests(unittest.TestCase):
    def test_legal_numbering_reaches_fifth_level(self):
        counts = {2: 1, 3: 2, 4: 3, 5: 1, 6: 1}
        self.assertEqual(format_section_number("legal", counts, 6), "I.B.3.a.i")

    def test_decimal_and_unumbered_modes(self):
        counts = {2: 1, 3: 2, 4: 3, 5: 1, 6: 1}
        self.assertEqual(format_section_number("decimal", counts, 6), "1.2.3.1.1")
        self.assertEqual(format_section_number("none", counts, 6), "")

    def test_defaults_preserve_existing_behavior(self):
        settings = LetterSettings()
        self.assertEqual(settings.section_numbering, "legal")
        self.assertFalse(settings.include_toc)

    def test_unknown_numbering_style_is_rejected(self):
        with self.assertRaises(ValueError):
            LetterSettings(section_numbering="outline-only")

    def test_outline_metadata_exists_without_visible_toc_or_numbers(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "document.md"
            source.write_text("## First\n\n### Second\n\nText", encoding="utf-8")
            renderer = ConfiguredPdfRenderer(
                source,
                root / "output.pdf",
                settings=LetterSettings(include_toc=False, section_numbering="none"),
            )
            outlines = [
                flowable.outline
                for flowable in renderer.build_story()
                if getattr(flowable, "outline", None)
            ]
            self.assertEqual(outlines, [("First", 0), ("Second", 1)])

    def test_toc_uses_same_numbered_section_labels(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "document.md"
            source.write_text(
                "## One\n### A\n### B\n#### Three\n##### Lower\n###### Roman\n",
                encoding="utf-8",
            )
            renderer = ConfiguredPdfRenderer(
                source,
                root / "output.pdf",
                settings=LetterSettings(include_toc=True, section_numbering="legal"),
            )
            labels = [label for _level, label in renderer._collect_section_entries()]
            self.assertEqual(labels[-1], "I.B.1.a.i Roman")
            self.assertTrue(renderer._toc_block([2, 2, 2, 3, 3, 3]))


if __name__ == "__main__":
    unittest.main()
