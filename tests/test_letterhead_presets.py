import unittest

from app import LETTERHEAD_PRESETS, app


class LetterheadPresetTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_index_loads_letterhead_preset_ui(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"/static/letterhead-presets.js", response.data)

    def test_whydrs_preset_assets_are_present(self):
        raster = LETTERHEAD_PRESETS["whydrs"]
        self.assertTrue(raster.exists())
        self.assertTrue(raster.with_suffix(".svg").exists())
        self.assertTrue(raster.with_suffix(".psd").exists())

    def test_whydrs_preset_renders_pdf(self):
        response = self.client.post(
            "/render",
            data={"markdown": "# Test\n\nPreset letterhead.", "letterhead_preset": "whydrs"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/pdf")
        self.assertTrue(response.data.startswith(b"%PDF-"))

    def test_unknown_letterhead_preset_is_rejected(self):
        response = self.client.post(
            "/render",
            data={"markdown": "# Test", "letterhead_preset": "unknown"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Unknown letterhead preset", response.get_json()["error"])


if __name__ == "__main__":
    unittest.main()
