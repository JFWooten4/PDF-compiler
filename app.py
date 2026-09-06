"""Small local web UI for configuring and rendering PDFs."""

from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename

from configured_renderer import DATE_FORMATS, IMAGE_TREATMENTS, ConfiguredPdfRenderer, LetterSettings

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024


def truthy(name: str) -> bool:
    return request.form.get(name) in {"1", "true", "on", "yes"}


@app.get("/")
def index():
    return render_template(
        "index.html",
        date_formats=DATE_FORMATS,
        image_treatments=IMAGE_TREATMENTS,
        today=date.today().isoformat(),
    )


@app.post("/render")
def render_pdf():
    source_upload = request.files.get("source")
    markdown = request.form.get("markdown", "")
    if not (source_upload and source_upload.filename) and not markdown.strip():
        return "Upload a Markdown file or paste Markdown text.", 400

    with TemporaryDirectory(prefix="pdf-compiler-") as temp:
        root = Path(temp)
        if source_upload and source_upload.filename:
            source_name = secure_filename(source_upload.filename) or "document.md"
            source = root / source_name
            source_upload.save(source)
        else:
            source = root / "document.md"
            source.write_text(markdown, encoding="utf-8")

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
            start_heading=request.form.get("start_heading", "").strip() or None,
        )
        renderer.build()
        payload = BytesIO(output.read_bytes())

    filename = secure_filename(request.form.get("output_name", "document.pdf")) or "document.pdf"
    if not filename.lower().endswith(".pdf"):
        filename += ".pdf"
    return send_file(payload, mimetype="application/pdf", download_name=filename, as_attachment=False)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
