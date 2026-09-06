"""Read-only validation for public HTTP(S) URLs in Markdown."""

from __future__ import annotations

from dataclasses import dataclass
import ipaddress
import re
import socket
from typing import Callable
from urllib.parse import urlsplit


@dataclass(frozen=True, slots=True)
class UrlValidationIssue:
    line: int
    column: int
    url: str
    message: str

    def as_dict(self) -> dict[str, object]:
        return {
            "line": self.line,
            "column": self.column,
            "url": self.url,
            "message": self.message,
        }


URL_RE = re.compile(r"https?://[^\s<>\"'`]*", re.IGNORECASE)
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")

Resolver = Callable[..., list[tuple]]


def _trim_url(raw: str) -> str:
    """Remove prose/Markdown punctuation that is not part of the URL."""
    value = raw.rstrip(".,;:!?")
    pairs = ((")", "("), ("]", "["), ("}", "{"))
    changed = True
    while changed and value:
        changed = False
        for closing, opening in pairs:
            if value.endswith(closing) and value.count(closing) > value.count(opening):
                value = value[:-1]
                changed = True
    return value


def validate_url_structure(url: str) -> str | None:
    """Validate URL syntax without performing DNS resolution."""
    if any(ord(character) < 32 for character in url):
        return "URL contains control characters."
    try:
        parsed = urlsplit(url)
    except ValueError:
        return "URL could not be parsed."
    if parsed.scheme.lower() not in {"http", "https"}:
        return "URL must use http:// or https://."
    if not parsed.hostname:
        return "URL is missing a hostname."
    try:
        port = parsed.port
    except ValueError:
        return "URL contains an invalid port."
    if port is not None and not 1 <= port <= 65535:
        return "URL contains an invalid port."
    return None


def _public_host_error(hostname: str, resolver: Resolver) -> str | None:
    host = hostname.rstrip(".").lower()
    if not host:
        return "URL is missing a hostname."
    if host == "localhost" or host.endswith(".localhost"):
        return "URL points to localhost rather than a public Internet host."

    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None

    if literal is not None:
        if not literal.is_global:
            return "URL points to a private, local, reserved, or otherwise non-public address."
        return None

    try:
        answers = resolver(host, None, type=socket.SOCK_STREAM)
    except (socket.gaierror, OSError):
        return "Hostname could not be resolved."

    addresses: set[str] = set()
    for answer in answers:
        sockaddr = answer[4]
        if sockaddr:
            addresses.add(sockaddr[0])
    if not addresses:
        return "Hostname could not be resolved."

    for address in addresses:
        try:
            parsed = ipaddress.ip_address(address)
        except ValueError:
            return "Hostname resolved to an invalid address."
        if not parsed.is_global:
            return "Hostname resolves to a private, local, reserved, or otherwise non-public address."
    return None


def validate_url(url: str, *, resolver: Resolver = socket.getaddrinfo) -> str | None:
    """Return an error message for an invalid/non-public HTTP(S) URL, else ``None``."""
    structural_error = validate_url_structure(url)
    if structural_error:
        return structural_error
    parsed = urlsplit(url)
    return _public_host_error(parsed.hostname or "", resolver)


def validate_urls(markdown: str, *, resolver: Resolver = socket.getaddrinfo) -> list[UrlValidationIssue]:
    """Validate HTTP(S) URLs outside code spans without modifying ``markdown``."""
    issues: list[UrlValidationIssue] = []
    host_cache: dict[str, str | None] = {}
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

        code_spans = [(match.start(), match.end()) for match in INLINE_CODE_RE.finditer(line)]
        for match in URL_RE.finditer(line):
            if any(start <= match.start() < end for start, end in code_spans):
                continue
            url = _trim_url(match.group(0))

            structural_error = validate_url_structure(url)
            if structural_error:
                error = structural_error
            else:
                parsed = urlsplit(url)
                host_key = (parsed.hostname or "").lower()
                if host_key in host_cache:
                    error = host_cache[host_key]
                else:
                    error = _public_host_error(parsed.hostname or "", resolver)
                    host_cache[host_key] = error

            if error:
                issues.append(
                    UrlValidationIssue(
                        line=line_number,
                        column=match.start() + 1,
                        url=url,
                        message=f"Invalid URL {url!r}: {error}",
                    )
                )

    return issues
