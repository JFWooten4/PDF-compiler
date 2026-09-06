"""Configurable letter/document presentation layered over :mod:`pdf_compiler`."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from html import escape
from io import BytesIO
from pathlib import Path

from PIL import Image as PILImage
from PIL import ImageChops, ImageOps
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from pdf_compiler import PdfRenderer


DATE_FORMATS = {
    "month_day_year": "September 6, 2026",
    "day_month_year": "4 May 2025",
    "iso": "2026-09-06",
    "us_numeric": "09/06/2026",
    "custom": "Custom strftime format",
}

IMAGE_TREATMENTS = {
    "preserve": "Preserve uploaded image",
    "trim": "Auto-trim empty padding",
    "print": "Auto-trim and optimize for monochrome printing",
}


@dataclass(slots=True)
class LetterSettings:
    """Presentation settings that are independent of the Markdown content."""

    show_date: bool = True
    date_format: str = "month_day_year"
    custom_date_format: str = "%B %d, %Y"
    date_value: str | None = None
    submission_subtitle: str = ""
    addressee: str = ""
    addressee_box: bool = True
    logo_treatment: str = "preserve"

    def __post_init__(self) -> None:
        if self.date_format not in DATE_FORMATS:
            raise ValueError(f"Unknown date format: {self.date_format}")
        if self.logo_treatment not in IMAGE_TREATMENTS:
            raise ValueError(f"Unknown image treatment: {self.logo_treatment}")
        if self.date_value:
            date.fromisoformat(self.date_value)


def format_header_date(settings: LetterSettings, *, today: date | None = None) -> str:
    """Format the configured letter date without platform-specific %-d behavior."""
    if not settings.show_date:
        return ""

    value = date.fromisoformat(settings.date_value) if settings.date_value else (today or date.today())
    if settings.date_format == "month_day_year":
        return f"{value.strftime('%B')} {value.day}, {value.year}"
    if settings.date_format == "day_month_year":
        return f"{value.day} {value.strftime('%B')} {value.year}"
    if settings.date_format == "iso":
        return value.isoformat()
    if settings.date_format == "us_numeric":
        return value.strftime("%m/%d/%Y")
    return value.strftime(settings.custom_date_format)


class ConfiguredPdfRenderer(PdfRenderer):
    """PdfRenderer with configurable letterhead and logo presentation."""

    def __init__(
        self,
        source: Path,
        output: Path,
        *,
        settings: LetterSettings | None = None,
        **kwargs,
    ):
        self.letter_settings = settings or LetterSettings()
        super().__init__(source, output, **kwargs)

    def _prepared_logo(self):
        """Return an ImageReader plus dimensions, keeping its BytesIO alive."""
        if not self.logo or not self.logo.exists():
            return None

        image = PILImage.open(self.logo).convert("RGBA")
        treatment = self.letter_settings.logo_treatment
        if treatment in {"trim", "print"}:
            background = PILImage.new("RGBA", image.size, "white")
            alpha = image.getchannel("A")
            background.paste(image, mask=alpha)
            diff = ImageChops.difference(background.convert("RGB"), PILImage.new("RGB", image.size, "white"))
            bbox = diff.getbbox()
            if bbox:
                image = image.crop(bbox)
        if treatment == "print":
            alpha = image.getchannel("A")
            gray = ImageOps.grayscale(image.convert("RGB"))
            gray = ImageOps.autocontrast(gray)
            image = PILImage.merge("RGBA", (gray, gray, gray, alpha))

        payload = BytesIO()
        image.save(payload, format="PNG")
        payload.seek(0)
        width, height = image.size
        return ImageReader(payload), width, height, payload

    def _addressee_block(self):
        if not self.letter_settings.addressee:
            return []
        text = "<br/>".join(escape(line) for line in self.letter_settings.addressee.splitlines())
        paragraph = Paragraph(text, self.styles["BodyX"])
        if not self.letter_settings.addressee_box:
            return [paragraph, Spacer(1, 8)]

        table = Table([[paragraph]], colWidths=[self.page_width - self.left - self.right])
        table.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#AAB2BD")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        return [table, Spacer(1, 10)]

    def build_story(self, extra_pages: int = 0):
        story = []
        if self.letter_settings.addressee:
            story.extend(self._addressee_block())
        story.extend(super().build_story(extra_pages))
        return story

    def draw_branding(self, canvas, doc):
        settings = self.letter_settings
        date_text = format_header_date(settings)
        subtitle = settings.submission_subtitle
        prepared = self._prepared_logo()
        has_brand = prepared is not None or self.wordmark
        has_header_text = bool(date_text or subtitle)
        if not has_brand and not has_header_text:
            return

        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#1F2937"))
        canvas.setLineWidth(0.7)

        if prepared is not None:
            reader, width, height, _payload = prepared
            target_width = 1.55 * inch
            target_height = target_width * height / width
            if target_height > 0.42 * inch:
                target_height = 0.42 * inch
                target_width = target_height * width / height
            canvas.drawImage(
                reader,
                doc.leftMargin,
                self.page_height - 0.63 * inch,
                width=target_width,
                height=target_height,
                preserveAspectRatio=True,
                mask="auto",
            )
        elif self.wordmark:
            canvas.setFont("Times-Bold", 18)
            canvas.drawString(doc.leftMargin, self.page_height - 0.58 * inch, self.wordmark)

        text_x = self.page_width - doc.rightMargin
        if date_text:
            canvas.setFont("Times-Roman", 10.5)
            canvas.drawRightString(text_x, self.page_height - 0.50 * inch, date_text)
        if subtitle:
            canvas.setFont("Times-Italic", 9.5)
            canvas.drawRightString(text_x, self.page_height - 0.66 * inch, subtitle)

        canvas.line(
            doc.leftMargin,
            self.page_height - 0.78 * inch,
            self.page_width - doc.rightMargin,
            self.page_height - 0.78 * inch,
        )
        canvas.restoreState()
