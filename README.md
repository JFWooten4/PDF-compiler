# PDF Compiler

A reusable Markdown-to-PDF renderer for polished, legal-style documents, with a browser configurator for presentation, metadata, validation, section structure, and output settings.

## Install

```bash
python -m pip install -r requirements.txt
```

## Web configurator

Run the web app:

```bash
python app.py
```

Then open `http://127.0.0.1:5000`.

The configurator accepts an uploaded Markdown file or pasted Markdown and lets you control the generated PDF without modifying the source text. Settings include:

- output filename
- PDF metadata: document title, author, subject, and keywords
- optional smart quotes in rendered text
- section numbering: legal form such as `I.B.3.a.i`, decimal form such as `1.2.3.4.5`, or no visible numbering
- optional visible table of contents using the generated section labels and page locations
- uploaded logo or text wordmark
- logo treatment: preserve as uploaded, auto-trim empty padding, or auto-trim and optimize for monochrome printing
- first-page date and date format, including `September 6, 2026`, `4 May 2025`, ISO, US numeric, or a custom `strftime` format
- submission subtitle such as `Submitted by email` or `Submitted via FedEx`
- addressee text with an optional bordered letterhead box
- separate first-page and remaining-page header text
- footer page-count styles: none, `1`, `Page 1`, `1 of 5`, or `Page 1 of 5`
- optional exact Markdown heading after which compilation begins
- legal-style preflight validation before rendering

Section structure is always written into the PDF outline/bookmark metadata. Turning off the visible table of contents only removes the TOC pages, and choosing no visible section numbering only removes numbering from displayed section labels; neither setting removes the PDF section outline.

The preflight validator reports line and column locations for required legal-style italics such as `_See_`, `_See, e.g.,_`, `_Id._`, `_Ibid._`, `_supra_`, `_infra_`, `_available at_`, and `_note_ 4`. These checks are case-insensitive. Validation is read-only and does not rewrite Markdown.

The rendered PDF opens inline in a new tab so the configurator remains available for another render.

## Command line

Render a Markdown file directly:

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
--smart-quotes         use typographic quotes in rendered text
```

For example:

```bash
python pdf_compiler.py comment.md \
  --output comment.pdf \
  --logo imgs/logo.png \
  --title "Comment Letter" \
  --author "WhyDRS" \
  --start-heading "Letter" \
  --smart-quotes
```

The additional presentation controls for subject/keywords metadata, visible TOC, section-numbering style, letterhead, running headers, and footer page counts are provided by the web configurator and `ConfiguredPdfRenderer`.

## Formatting and document behavior

The compiler supports:

- US Letter output with Times typography
- hierarchical section numbering for nested Markdown headings, including legal and decimal styles
- PDF outline/bookmark entries for sections regardless of visible TOC settings
- an optional visible table of contents with hierarchical indentation and page numbers
- Markdown footnotes placed at the bottom of the page where referenced, including continuation pages
- basic bold, italic, inline code, links, block quotes, lists, rules, and local images
- optional first-page logo or text wordmark
- configurable PDF metadata
- configurable first-page letterhead date and submission subtitle
- optional boxed addressee block
- separate first-page and later-page headers
- selectable footer page-count formats using the final PDF page count
- optional logo cleanup for padded assets and monochrome printing
- optional smart-quote rendering without changing the Markdown source
- read-only legal-style validation before PDF generation

The rendering engine, presentation settings, and validation layer are kept separate so document generation does not alter source content.
