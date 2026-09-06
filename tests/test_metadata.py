from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from configured_renderer import ConfiguredPdfRenderer


class RecordingCanvas:
    def __init__(self):
        self.values = {}

    def setTitle(self, value):
        self.values["title"] = value

    def setAuthor(self, value):
        self.values["author"] = value

    def setSubject(self, value):
        self.values["subject"] = value

    def setKeywords(self, value):
        self.values["keywords"] = value


class MetadataTests(unittest.TestCase):
    def test_configured_metadata_is_applied(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "filing.md"
            source.write_text("## Body\n\nText", encoding="utf-8")
            renderer = ConfiguredPdfRenderer(
                source,
                root / "output.pdf",
                title="Transfer Agent Comment Letter",
                author="BlockTransfer",
                subject="SEC transfer agent rulemaking",
                keywords="transfer agents, SEC, comment letter",
            )
            canvas = RecordingCanvas()
            renderer.apply_metadata(canvas)

            self.assertEqual(canvas.values["title"], "Transfer Agent Comment Letter")
            self.assertEqual(canvas.values["author"], "BlockTransfer")
            self.assertEqual(canvas.values["subject"], "SEC transfer agent rulemaking")
            self.assertEqual(canvas.values["keywords"], "transfer agents, SEC, comment letter")

    def test_title_defaults_to_source_stem(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "filing.md"
            source.write_text("## Body\n\nText", encoding="utf-8")
            renderer = ConfiguredPdfRenderer(source, root / "output.pdf")
            self.assertEqual(renderer.title, "filing")


if __name__ == "__main__":
    unittest.main()
