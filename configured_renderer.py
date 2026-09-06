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

PAGE_NUMBER_STYLES = {
    "none": "No page count",
    "number": "1",
    "page_number": "Page 1",
    "number_of_total": "1 of 5",
    "page_number_of_total": "Page 1 of 5",
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
    first_page_header: str = ""
    remaining_page_header: str = ""
    page_number_style: str = "none"

    def __post_init__(self) -> None:
        if self.date_format not in DATE_FORMATS:
            raise ValueError(f"Unknown date format: {self.date_format}")
        if self.logo_treatment not in IMAGE_TREATMENTS:
            raise ValueError(f"Unknown image treatment: {self.logo_treatment}")
        if self.page_number_style not in PAGE_NUMBER_STYLES:
            raise ValueError(f"Unknown page-number style: {self.page_number_style}")
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


def format_page_number(style: str, page: int, total: int) -> str:
    """Format one footer page-count label."""
    if style == "none":
        return ""
    if style == "number":
        return str(page)
    if style == "page_number":
        return f"Page {page}"
    if style == "number_of_total":
        return f"{page} of {total}"
    if style == "page_number_of_total":
        return f"Page {page} of {total}"
    raise ValueError(f"Unknown page-number style: {style}")


class ConfiguredPdfRenderer(PdfRenderer):
    """PdfRenderer with configurable letterhead and page presentation."""

    def __init__(
        self,
        source: Path,
        output: Path,
        *,
        settings: LetterSettings | None = None,
        subject: str | None = None,
        keywords: str | None = None,
        **kwargs,
    ):
        self.letter_settings = settings or LetterSettings()
        self.subject = subject or ""
        self.keywords = keywords or ""
        self._total_pages = 0
        super().__init__(source, output, **kwargs)
        if self.letter_settings.first_page_header or self.letter_settings.remaining_page_header:
            self.top = max(self.top, 1.10 * inch)

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

    def apply_metadata(self, canvas) -> None:
        """Apply configurable PDF document-info metadata to the output canvas."""
        canvas.setTitle(self.title)
        canvas.setAuthor(self.author)
        if self.subject:
            canvas.setSubject(self.subject)
        if self.keywords:
            canvas.setKeywords(self.keywords)

    def draw_branding(self, canvas, doc):
        settings = self.letter_settings
        date_text = format_header_date(settings)
        subtitle = settings.submission_subtitle
        first_header = settings.first_page_header.strip()
        prepared = self._prepared_logo()
        has_brand = prepared is not None or self.wordmark
        has_header_text = bool(date_text or subtitle or first_header)
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

        line_offset = 0.78
        if first_header:
            canvas.setFont("Times-Roman", 9.5)
            canvas.drawCentredString(self.page_width / 2, self.page_height - 0.77 * inch, first_header)
            line_offset = 0.92

        canvas.line(
            doc.leftMargin,
            self.page_height - line_offset * inch,
            self.page_width - doc.rightMargin,
            self.page_height - line_offset * inch,
        )
        canvas.restoreState()

    def draw_remaining_header(self, canvas, doc):
        text = self.letter_settings.remaining_page_header.strip()
        if not text:
            return
        canvas.saveState()
        canvas.setFillColor(colors.HexColor("#374151"))
        canvas.setStrokeColor(colors.HexColor("#9AA3AE"))
        canvas.setFont("Times-Roman", 9.5)
        canvas.drawCentredString(self.page_width / 2, self.page_height - 0.55 * inch, text)
        canvas.setLineWidth(0.5)
        canvas.line(
            doc.leftMargin,
            self.page_height - 0.73 * inch,
            self.page_width - doc.rightMargin,
            self.page_height - 0.73 * inch,
        )
        canvas.restoreState()

    def draw_page_number(self, canvas, page: int) -> None:
        label = format_page_number(self.letter_settings.page_number_style, page, self._total_pages)
        if not label:
            return
        canvas.saveState()
        canvas.setFillColor(colors.HexColor("#4B5563"))
        canvas.setFont("Times-Roman", 8.5)
        canvas.drawCentredString(self.page_width / 2, 0.14 * inch, label)
        canvas.restoreState()

    def continuation_pages_needed(self, page_refs: dict[int, list[int]], base_pages: int) -> int:
        extra = super().continuation_pages_needed(page_refs, base_pages)
        self._total_pages = base_pages + extra
        return extra

    def page_drawer(self, page_refs: dict[int, list[int]]):
        carry: list[Paragraph] = []

        def draw(canvas, doc):
            nonlocal carry
            self.apply_metadata(canvas)
            if doc.page == 1:
                self.draw_branding(canvas, doc)
            else:
                self.draw_remaining_header(canvas, doc)

            refs = page_refs.get(doc.page, [])
            items = carry + [self.footnote_paragraph(number) for number in refs]
            carry = []
            if items:
                canvas.saveState()
                yline = 0.30 * inch + self.foot_top
                canvas.setStrokeColor(colors.HexColor("#B8C0CC"))
                canvas.setLineWidth(0.45)
                canvas.line(doc.leftMargin, yline, self.page_width - doc.rightMargin, yline)
                y = yline - 0.08 * inch
                bottom_guard = 0.34 * inch if self.letter_settings.page_number_style != "none" else 0.24 * inch

                for index, paragraph in enumerate(items):
                    available = y - bottom_guard
                    _, height = paragraph.wrap(self.max_foot_width, available)
                    if height <= available:
                        y -= height
                        paragraph.drawOn(canvas, doc.leftMargin, y)
                        y -= 0.02 * inch
                        continue

                    pieces = paragraph.split(self.max_foot_width, available)
                    if pieces:
                        first = pieces[0]
                        _, first_height = first.wrap(self.max_foot_width, available)
                        if first_height <= available:
                            y -= first_height
                            first.drawOn(canvas, doc.leftMargin, y)
                            carry = pieces[1:] + items[index + 1 :]
                            break
                    carry = items[index:]
                    break

                canvas.restoreState()

            self.draw_page_number(canvas, doc.page)

        draw.carry = lambda: carry
        return draw
