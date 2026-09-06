import socket
import unittest

from url_validator import validate_urls


def public_resolver(host, port, **kwargs):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port or 0))]


def missing_resolver(host, port, **kwargs):
    raise socket.gaierror("not found")


def private_resolver(host, port, **kwargs):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", port or 0))]


def https_supported(host, port, resolver):
    return True


def https_unavailable(host, port, resolver):
    return False


class UrlValidatorTests(unittest.TestCase):
    def test_accepts_markdown_and_bare_public_urls(self):
        markdown = "[Source](https://example.com/path) and https://example.com/other."
        self.assertEqual(validate_urls(markdown, resolver=public_resolver), [])

    def test_flags_unresolvable_hostname(self):
        issues = validate_urls("See https://does-not-exist.invalid/path.", resolver=missing_resolver)
        self.assertEqual(len(issues), 1)
        self.assertIn("could not be resolved", issues[0].message)
        self.assertEqual(issues[0].line, 1)
        self.assertEqual(issues[0].column, 5)

    def test_flags_malformed_http_url(self):
        issues = validate_urls("Broken: https://", resolver=public_resolver)
        self.assertEqual(len(issues), 1)
        self.assertIn("missing a hostname", issues[0].message)

    def test_rejects_private_network_targets(self):
        issues = validate_urls("http://localhost/test\nhttps://internal.example/test", resolver=private_resolver)
        self.assertEqual(len(issues), 2)
        self.assertIn("localhost", issues[0].message)
        self.assertIn("private", issues[1].message)

    def test_prefers_https_when_available(self):
        issues = validate_urls(
            "Source: http://example.com/path",
            resolver=public_resolver,
            https_checker=https_supported,
        )
        self.assertEqual(len(issues), 1)
        self.assertIn("https://example.com/path", issues[0].message)
        self.assertIn("HTTPS is available", issues[0].message)

    def test_allows_http_when_https_is_unavailable(self):
        issues = validate_urls(
            "Source: http://example.com/path",
            resolver=public_resolver,
            https_checker=https_unavailable,
        )
        self.assertEqual(issues, [])

    def test_root_url_must_not_end_in_slash(self):
        issues = validate_urls(
            "Source: https://example.com/",
            resolver=public_resolver,
        )
        self.assertEqual(len(issues), 1)
        self.assertIn("https://example.com", issues[0].message)
        self.assertIn("root URLs must not end", issues[0].message)

    def test_http_root_url_reports_combined_canonical_form(self):
        issues = validate_urls(
            "Source: http://example.com/",
            resolver=public_resolver,
            https_checker=https_supported,
        )
        self.assertEqual(len(issues), 1)
        self.assertIn("https://example.com", issues[0].message)
        self.assertIn("HTTPS is available", issues[0].message)
        self.assertIn("root URLs must not end", issues[0].message)

    def test_non_root_trailing_slash_is_allowed(self):
        self.assertEqual(
            validate_urls("https://example.com/path/", resolver=public_resolver),
            [],
        )

    def test_ignores_inline_and_fenced_code(self):
        markdown = """`https://bad.invalid/x`
```
https://bad.invalid/y
```
"""
        self.assertEqual(validate_urls(markdown, resolver=missing_resolver), [])

    def test_strips_markdown_closing_parenthesis_and_prose_punctuation(self):
        issues = validate_urls("[Source](https://bad.invalid/path).", resolver=missing_resolver)
        self.assertEqual(issues[0].url, "https://bad.invalid/path")


if __name__ == "__main__":
    unittest.main()
