"""Read-only preflight checks for legal-style Markdown conventions."""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    line: int
    column: int
    term: str
    message: str
    excerpt: str

    def as_dict(self) -> dict[str, object]:
        return {
            "line": self.line,
            "column": self.column,
            "term": self.term,
            "message": self.message,
            "excerpt": self.excerpt,
        }


EMPHASIS_RE = re.compile(
    r"\*\*\*[^*\n]+?\*\*\*|___[^_\n]+?___|"
    r"(?<!\*)\*[^*\n]+?\*(?!\*)|(?<!_)_[^_\n]+?_(?!_)|"
    r"<(?:em|i)\b[^>]*>.*?</(?:em|i)>",
    re.IGNORECASE,
)
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")

RULES: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "See",
        re.compile(
            r"\b(?:but\s+see|see)"
            r"(?:\s+(?:also|generally))?"
            r"(?:,\s*e\.g\.,?)?",
            re.IGNORECASE,
        ),
        "Italicize legal citation signals such as _See_, _See also_, _But see_, or _See, e.g.,_.",
    ),
    (
        "Id./Ibid.",
        re.compile(r"\b(?:id|ibid)\.", re.IGNORECASE),
        "Italicize _Id._ and _Ibid._ when used in citations.",
    ),
    (
        "supra/infra",
        re.compile(r"\b(?:supra|infra)\b", re.IGNORECASE),
        "Italicize supra and infra when used in citations.",
    ),
    (
        "available at",
        re.compile(r"\bavailable\s+at\b", re.IGNORECASE),
        "Italicize the citation phrase _available at_.",
    ),
    (
        "note",
        re.compile(r"\bnote\b(?=\s+\d+\b)", re.IGNORECASE),
        "Italicize note when followed by a note number, for example _note_ 4.",
    ),
)


def _spans(pattern: re.Pattern[str], line: str) -> list[tuple[int, int]]:
    return [(match.start(), match.end()) for match in pattern.finditer(line)]


def _covered(start: int, end: int, spans: list[tuple[int, int]]) -> bool:
    return any(span_start <= start and end <= span_end for span_start, span_end in spans)


def _formatting_ranges(match: re.Match[str]) -> list[tuple[int, int]]:
    """Return only the markup delimiters/tags for an emphasis match."""
    text = match.group(0)
    start, end = match.span()
    if text.startswith("***") and text.endswith("***"):
        return [(start, start + 3), (end - 3, end)]
    if text.startswith("___") and text.endswith("___"):
        return [(start, start + 3), (end - 3, end)]
    if text.startswith("*") and text.endswith("*"):
        return [(start, start + 1), (end - 1, end)]
    if text.startswith("_") and text.endswith("_"):
        return [(start, start + 1), (end - 1, end)]
    return [
        (start + tag.start(), start + tag.end())
        for tag in re.finditer(r"</?(?:em|i)\b[^>]*>", text, re.IGNORECASE)
    ]


def _detection_text(line: str) -> tuple[str, list[int], list[tuple[int, int]]]:
    """Strip emphasis markup for matching while preserving raw offsets."""
    emphasis_matches = list(EMPHASIS_RE.finditer(line))
    emphasis_spans = [(match.start(), match.end()) for match in emphasis_matches]
    skipped: set[int] = set()
    for match in emphasis_matches:
        for start, end in _formatting_ranges(match):
            skipped.update(range(start, end))

    chars: list[str] = []
    raw_positions: list[int] = []
    for index, character in enumerate(line):
        if index in skipped:
            continue
        chars.append(character)
        raw_positions.append(index)
    return "".join(chars), raw_positions, emphasis_spans


def validate_legal_style(markdown: str) -> list[ValidationIssue]:
    """Return legal-style violations without modifying ``markdown``."""
    issues: list[ValidationIssue] = []
    in_fence = False
    fence_marker: str | None = None

    for line_number, line in enumerate(markdown.splitlines(), start=1):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            marker = stripped[:3]
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif marker == fence_marker:
                in_fence = False
                fence_marker = None
            continue
        if in_fence:
            continue

        detection, raw_positions, emphasis_spans = _detection_text(line)
        code_spans = _spans(INLINE_CODE_RE, line)

        for term, pattern, message in RULES:
            for match in pattern.finditer(detection):
                if match.start() == match.end() or not raw_positions:
                    continue
                raw_start = raw_positions[match.start()]
                raw_end = raw_positions[match.end() - 1] + 1
                if _covered(raw_start, raw_end, code_spans):
                    continue
                if _covered(raw_start, raw_end, emphasis_spans):
                    continue
                issues.append(
                    ValidationIssue(
                        line=line_number,
                        column=raw_start + 1,
                        term=term,
                        message=message,
                        excerpt=line.strip(),
                    )
                )

    return issues
