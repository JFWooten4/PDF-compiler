# Inline emoji text implementation

Status: scaffold only. The renderer still uses bundled Twemoji images.

## Requested behavior

Preserve emoji as inline Unicode text by default instead of replacing it with
images. The user wants the reader's device to render the characters using its
own emoji appearance. Selectable text using a fixed embedded font is a possible
fallback, but has not been accepted as equivalent to that request.

## Establish the PDF constraint first

PDF text requires a font and character mapping. Passing raw emoji through the
current Times font produces missing glyphs; removing image substitution alone
does not implement this feature. ReportLab supports embedded TrueType fonts,
but embedding a font fixes its appearance rather than adopting the reader's
native emoji style. See the [ReportLab font documentation](https://docs.reportlab.com/reportlab/userguide/ch3_fonts/).

1. Prototype Unicode PDF text with a nonembedded emoji font reference and an
   explicit Unicode mapping outside the production renderer. Verify the actual
   result in macOS Preview and a PDF.js viewer, including extraction and copying.
   Do not assume either viewer supplies browser-style emoji fallback or supports
   the same sequences.
2. Record whether native appearance is feasible and portable. If it is not,
   explain the limitation before treating an embedded font as the solution.
   An HTML output could supply native browser emoji rendering, but adding that
   output is a separate product decision.
3. If implementing an embedded-font alternative, select a redistributable font
   with suitable glyph coverage and shaping support. Document its license and
   whether output is monochrome or color. Do not bundle Apple's system fonts.

## Implementation map

### Requested emoji selector

Add a selector with all seven options below and small visual previews showing
how each set renders emoji. This is a requested feature specification only;
do not implement the selector as part of this scaffold.

| Option | Visual style |
| --- | --- |
| Fluent Emoji | Rich, polished, dimensional style |
| Noto Emoji | Rounded Google/Android style |
| OpenMoji | Bold outlines and color |
| Twemoji | Familiar flat style |
| Blobmoji | Classic Google blob style |
| Emojitwo | Older EmojiOne cartoon style |
| Mutant Standard | Distinctive alternative designs |

These descriptions summarize the user's supplied comparison, not verified
current coverage, maintenance, or license claims. Before implementation, verify
each project's current release, asset and font licenses, attribution requirements,
and available output formats from its primary sources. Sets may provide artwork
rather than fonts; do not label image-based PDF output as selectable emoji text.
The selector request does not resolve the native-versus-embedded-font constraint.

Selector behavior:

- Show previews from the actual selected release of each set, rather than using
  the browser's native emoji characters to stand in for those designs. Prefer
  several emoji from the current document and use a sample when it has none.
- Keep all seven options visible. Mark an option unavailable and disable its
  selection if it cannot render every emoji sequence used in the document.
  Explain which sequences are unsupported beside the option.
- Determine coverage from the actual assets or font/shaping backend that will
  generate the PDF. A set's Unicode version or its name alone is insufficient.
- Check full sequences, including variation selectors, joined emoji, flags,
  skin tones, and keycaps. Individual component coverage does not establish
  support for a combined sequence. An unsupported sequence must not silently
  split into separate symbols or fall back to another set.
- Recompute availability when the source or any rendered text field changes,
  including titles, headings, addressees, and headers. Inspect visible text, not
  URLs or markup attributes; respect uploaded-file precedence over pasted text.
- If the selected set becomes incompatible, show the missing sequences and block
  compilation until a compatible choice is made or the content is corrected.
  Do not silently switch sets or omit characters. If none support the complete
  document, explain that no set is currently available for that content.
- Preserve the selection per render request and validate coverage on the server
  as well as in the UI. Unknown or failed coverage checks must not appear as
  confirmed support.
- Make previews and disabled reasons accessible with text labels and keyboard
  navigation. Clearly describe whether each backend produces text or images.

### Renderer integration

- `emoji_renderer.py`: separate the current image substitution from the proposed
  text backend. Keep `_dash_markup` behavior and leave markup attributes,
  destinations, and anchors untouched. Preserve variation selectors, skin tones,
  regional indicators, keycaps, and zero-width joiners in text sequences.
- `EmojiParagraph`: apply the selected backend consistently when constructing
  paragraphs; preserve the existing `frags` path used during paragraph splitting.
  Do not use mutable process-wide settings for individual render requests.
- `pdf_compiler.py`: propagate any rendering option through the base renderer,
  paragraph construction, list items, and CLI arguments.
- `configured_renderer.py`, `typography_renderer.py`, and `first_page_layout.py`:
  cover all directly constructed paragraphs, headings, TOC entries, visible
  titles, addressees, and running headers. Keep ordinary body typography intact.
- `app.py` and `templates/index.html`: implement the seven-set selector and its
  coverage checks. Make text the default only when it renders correctly. Any retained
  image mode must be explicit, not a silent fallback that contradicts the request.
- `README.md`: replace the existing claim that emoji always render as images
  once behavior changes; describe the actual viewer and font limitations.

Do not silently drop unsupported emoji, replace them with images in text mode,
or claim that an embedded font produces reader-native appearance.

## Validation to run during implementation

Use `examples/emoji-text.md` as the shared visual and text-extraction fixture.
The scaffold does not change production behavior or replace the current tests.

1. Extend `tests/test_emoji_renderer.py` to assert original Unicode sequences
   survive the text path and do not create image fragments. Retain coverage of
   links, dash normalization, wrapping, and any explicitly supported image mode.
2. Generate PDFs through both the CLI and web renderer. Check emoji-only input
   introduces no image XObjects, has a usable Unicode mapping, and extracts the
   original sequences. Text appearing in paragraph fragments is insufficient.
3. Verify selection and copying from real PDF viewers, including headings and
   TOC entries. Compare extracted characters by code point, including invisible
   sequence characters.
4. Inspect visual output at normal and high zoom in Preview and PDF.js. Verify
   no missing glyphs, clipping, unintended spacing, or broken joined sequences.
   Test wrapping, multi-page documents, and the light/dark viewer presentation.
5. Run the existing emoji, typography, heading/TOC, and web-render tests using the
   repository's available Python environment. Report separately what was tested
   structurally, what was seen in viewers, and what remains viewer-dependent.
6. Verify the selector shows all seven sets with real previews. Exercise complete
   coverage, missing joined sequences, no compatible sets, upload precedence,
   header-only emoji, and edits that invalidate the selected set. Confirm server
   validation rejects an incompatible set even when UI checks are bypassed.

## Completion criteria

- Default emoji are PDF text, selectable and copyable as the original Unicode.
- No emoji images are introduced in text mode.
- The example renders correctly across the tested viewers and all applicable
  document surfaces.
- Reader-native appearance is either demonstrated or explicitly identified as
  unsupported; fixed embedded-font appearance is not presented as native.
- Font licensing, deployment requirements, and supported behavior are documented.
