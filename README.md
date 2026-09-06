# PDF Compiler

Go from Markdown to document, with flair.

This repository is the reusable home for the Markdown-to-PDF renderer first developed in [WhyDRS/SEC-Comments#67](https://github.com/WhyDRS/SEC-Comments/pull/67). The migration removes the original OCC- and WhyDRS-specific paths and metadata while retaining the document-formatting behavior that made the renderer useful.

## Install

```bash
python -m pip install -r requirements.txt
```

## Web configurator

The simplest interface is the local web app:

```bash
python app.py
```

Then open `http://127.0.0.1:5000`.

The configurator lets you upload or paste Markdown and choose presentation settings before rendering the PDF in a new tab. Current controls include:

- uploaded logo or text wordmark
- logo treatment: preserve as uploaded, auto-trim empty padding, or auto-trim and optimize for monochrome printing
- first-page date and date format (`September 6, 2026`, `6 September 2026`, ISO, US numeric, or a custom `strftime` format)
- submission subtitle such as `Submitted by email` or `Submitted via FedEx`
- addressee text with an optional bordered letterhead box
- PDF title and author metadata
- optional exact Markdown heading to begin compilation after
- output filename

The form stays open while the rendered PDF opens inline in a new tab, which makes it easy to adjust settings and render another version.

## Command line

The original renderer remains available directly:

```bash
python pdf_compiler.py path/to/document.md
```

The default output is the source path with a `.pdf` suffix.

Useful options:

```text
--output PATH          choose the output PDF
--logo PATH            add an image logo to the first page
--wordmark TEXT        use a text wordmark when no logo is supplied
--title TEXT           set PDF title metadata
--author TEXT          set PDF author metadata
--start-heading TEXT   compile only content after an exact Markdown heading
```

For example, the original comment-letter workflow can be represented without hard-coded repository paths:

```bash
python pdf_compiler.py comment.md \
  --output comment.pdf \
  --logo imgs/logo.png \
  --title "Comment Letter" \
  --author "WhyDRS" \
  --start-heading "Letter"
```

## Current formatting

The compiler currently supports:

- US Letter output with Times typography
- legal-style numbering for nested Markdown headings
- PDF outline/bookmark entries for headings
- Markdown footnotes placed at the bottom of the page where referenced, including continuation pages
- basic bold, italic, inline-code, links, block quotes, lists, rules, and local images
- optional first-page logo or text wordmark
- configurable PDF title and author metadata
- configurable first-page letterhead date and submission subtitle through the web interface
- optional boxed addressee block
- optional logo cleanup for padded assets and monochrome printing

The renderer and its presentation settings are kept separate so the document engine can continue to grow without tying it to a particular interface.
