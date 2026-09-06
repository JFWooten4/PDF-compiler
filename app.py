"""Small web UI for configuring, validating, and rendering PDFs."""

from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.utils import secure_filename

from configured_renderer import (
    DATE_FORMATS,
    IMAGE_TREATMENTS,
    PAGE_NUMBER_STYLES,
    SECTION_NUMBERING_STYLES,
    ConfiguredPdfRenderer,
    LetterSettings,
)
from legal_style_validator import validate_legal_style

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024


def truthy(name: str) -> bool:
    return request.form.get(name) in {"1", "true", "on", "yes"}


def submitted_markdown() -> tuple[str | None, str | None]:
    source_upload = request.files.get("source")
    markdown = request.form.get("markdown", "")
    if source_upload and source_upload.filename:
        try:
            text = source_upload.read().decode("utf-8-sig")
        except UnicodeDecodeError:
            return None, "Markdown uploads must be UTF-8 text."
        finally:
            source_upload.stream.seek(0)
        return text, None
    if markdown.strip():
        return markdown, None
    return None, "Upload a Markdown file or paste Markdown text."


@app.get("/")
def index():
    return render_template(
        "index.html",
        date_formats=DATE_FORMATS,
        image_treatments=IMAGE_TREATMENTS,
        page_number_styles=PAGE_NUMBER_STYLES,
        section_numbering_styles=SECTION_NUMBERING_STYLES,
        today=date.today().isoformat(),
    )


@app.post("/validate")
def validate_markdown():
    markdown, error = submitted_markdown()
    if error:
        return jsonify({"valid": False, "error": error, "issues": []}), 400

    issues = validate_legal_style(markdown or "")
    return jsonify(
        {
            "valid": not issues,
            "issues": [issue.as_dict() for issue in issues],
        }
    )


@app.post("/render")
def render_pdf():
    markdown, error = submitted_markdown()
    if error:
        return jsonify({"error": error}), 400

    issues = validate_legal_style(markdown or "")
    if issues:
        return (
            jsonify(
                {
                    "error": "Legal-style preflight failed. The source was not modified and no PDF was generated.",
                    "issues": [issue.as_dict() for issue in issues],
                }
            ),
            422,
        )

    source_upload = request.files.get("source")
    with TemporaryDirectory(prefix="pdf-compiler-") as temp:
        root = Path(temp)
        if source_upload and source_upload.filename:
            source_name = secure_filename(source_upload.filename) or "document.md"
            source = root / source_name
            source.write_text(markdown or "", encoding="utf-8")
        else:
            source = root / "document.md"
            source.write_text(markdown or "", encoding="utf-8")

        logo = None
        logo_upload = request.files.get("logo")
        if logo_upload and logo_upload.filename:
            logo_name = secure_filename(logo_upload.filename) or "logo.png"
            logo = root / logo_name
            logo_upload.save(logo)

        settings = LetterSettings(
            show_date=truthy("show_date"),
            date_format=request.form.get("date_format", "month_day_year"),
            custom_date_format=request.form.get("custom_date_format", "%B %d, %Y"),
            date_value=request.form.get("date_value") or None,
            submission_subtitle=request.form.get("submission_subtitle", "").strip(),
            addressee=request.form.get("addressee", "").strip(),
            addressee_box=truthy("addressee_box"),
            logo_treatment=request.form.get("logo_treatment", "preserve"),
            first_page_header=request.form.get("first_page_header", "").strip(),
            remaining_page_header=request.form.get("remaining_page_header", "").strip(),
            page_number_style=request.form.get("page_number_style", "none"),
            include_toc=truthy("include_toc"),
            section_numbering=request.form.get("section_numbering", "legal"),
        )

        output = root / "output.pdf"
        renderer = ConfiguredPdfRenderer(
            source,
            output,
            settings=settings,
            logo=logo,
            wordmark=request.form.get("wordmark", "").strip() or None,
            title=request.form.get("title", "").strip() or None,
            author=request.form.get("author", "").strip() or None,
            subject=request.form.get("subject", "").strip() or None,
            keywords=request.form.get("keywords", "").strip() or None,
            start_heading=request.form.get("start_heading", "").strip() or None,
            smart_quotes=truthy("smart_quotes"),
        )
        renderer.build()
        payload = BytesIO(output.read_bytes())

    filename = secure_filename(request.form.get("output_name", "document.pdf")) or "document.pdf"
    if not filename.lower().endswith(".pdf"):
        filename += ".pdf"
    return send_file(payload, mimetype="application/pdf", download_name=filename, as_attachment=False)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
