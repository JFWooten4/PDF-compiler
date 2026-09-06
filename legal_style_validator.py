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
        re.compile(r"\b(?:See(?:\s+(?:also|generally))?|But\s+see)\b"),
        "Italicize legal citation signals such as _See_, _See also_, or _But see_.",
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

        emphasis_spans = _spans(EMPHASIS_RE, line)
        code_spans = _spans(INLINE_CODE_RE, line)

        for term, pattern, message in RULES:
            for match in pattern.finditer(line):
                if _covered(match.start(), match.end(), code_spans):
                    continue
                if _covered(match.start(), match.end(), emphasis_spans):
                    continue
                issues.append(
                    ValidationIssue(
                        line=line_number,
                        column=match.start() + 1,
                        term=term,
                        message=message,
                        excerpt=line.strip(),
                    )
                )

    return issues
