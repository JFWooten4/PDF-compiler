# PDF Compiler

Go from Markdown to document, with flair.

This repository is the reusable home for the Markdown-to-PDF renderer first developed in [WhyDRS/SEC-Comments#67](https://github.com/WhyDRS/SEC-Comments/pull/67). The migration removes the original OCC- and WhyDRS-specific paths and metadata while retaining the document-formatting behavior that made the renderer useful.

## Install

```bash
python -m pip install -r requirements.txt
```

## Use

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

The initial extraction is intentionally close to the renderer from PR #67. This repository is the place to grow the more general document interface discussed there, including structured letterhead fields such as organization/address information and submission dates.
