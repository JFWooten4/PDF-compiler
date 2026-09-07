"""First-page letterhead layout with a visible title separate from PDF metadata."""

from __future__ import annotations

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph

from configured_renderer import ConfiguredPdfRenderer, format_header_date


class FirstPagePdfRenderer(ConfiguredPdfRenderer):
    """Configured renderer with a filing-style first-page identity block."""

    def __init__(self, *args, visible_document_title: str | None = None, **kwargs):
        self.visible_document_title = (visible_document_title or "").strip()
        super().__init__(*args, **kwargs)

        settings = self.letter_settings
        has_letterhead_row = bool(
            self.logo
            or self.wordmark
            or self.visible_document_title
            or format_header_date(settings)
            or settings.submission_subtitle.strip()
        )
        if settings.first_page_header.strip() and has_letterhead_row:
            self.top = max(self.top, 1.95 * inch)
        elif has_letterhead_row:
            self.top = max(self.top, 1.55 * inch)

    def draw_branding(self, canvas, doc):
        """Draw the first-page header first, then logo/title/date beneath it."""
        settings = self.letter_settings
        date_text = format_header_date(settings)
        subtitle = settings.submission_subtitle.strip()
        first_header = settings.first_page_header.strip()
        prepared = self._prepared_logo()
        has_brand = prepared is not None or self.wordmark
        has_letterhead_row = bool(has_brand or self.visible_document_title or date_text or subtitle)
        if not first_header and not has_letterhead_row:
            return

        canvas.saveState()
        canvas.setFillColor(colors.black)

        # The first-page header is deliberately the highest visible document element.
        if first_header:
            canvas.setFont("Times-Bold", 9.5)
            canvas.drawCentredString(self.page_width / 2, self.page_height - 0.36 * inch, first_header)

        if has_letterhead_row:
            row_top = 0.80 if first_header else 0.40
            row_top_y = self.page_height - row_top * inch

            if prepared is not None:
                reader, width, height, _payload = prepared
                target_width = 1.85 * inch
                target_height = target_width * height / width
                if target_height > 0.52 * inch:
                    target_height = 0.52 * inch
                    target_width = target_height * width / height
                canvas.drawImage(
                    reader,
                    doc.leftMargin,
                    row_top_y - target_height,
                    width=target_width,
                    height=target_height,
                    preserveAspectRatio=True,
                    mask="auto",
                )
            elif self.wordmark:
                canvas.setFont("Times-Bold", 18)
                canvas.drawString(doc.leftMargin, row_top_y - 0.31 * inch, self.wordmark)

            if self.visible_document_title:
                title_left = doc.leftMargin + (2.05 * inch if has_brand else 0)
                title_right = self.page_width - doc.rightMargin
                title_width = max(1.0 * inch, title_right - title_left)
                title_style = ParagraphStyle(
                    "VisibleDocumentTitle",
                    fontName="Times-Bold",
                    fontSize=14.5,
                    leading=17,
                    alignment=1,
                    spaceBefore=0,
                    spaceAfter=0,
                )
                rendered_title, _ = self.markdown_inline(self.visible_document_title, False)
                title = Paragraph(rendered_title, title_style)
                _, title_height = title.wrap(title_width, 0.62 * inch)
                title.drawOn(canvas, title_left, row_top_y - title_height)

            text_x = self.page_width - doc.rightMargin
            if date_text:
                canvas.setFont("Times-Roman", 10.5)
                canvas.drawRightString(text_x, self.page_height - (row_top + 0.62) * inch, date_text)
            if subtitle:
                canvas.setFont("Times-Bold", 9.5)
                canvas.drawRightString(text_x, self.page_height - (row_top + 0.79) * inch, subtitle)

            canvas.setStrokeColor(colors.HexColor("#1F2937"))
            canvas.setLineWidth(0.7)
            canvas.line(
                doc.leftMargin,
                self.page_height - (row_top + 0.98) * inch,
                self.page_width - doc.rightMargin,
                self.page_height - (row_top + 0.98) * inch,
            )

        canvas.restoreState()
