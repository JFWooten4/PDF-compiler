import socket
import unittest

from url_validator import validate_urls


def public_resolver(host, port, **kwargs):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]


def missing_resolver(host, port, **kwargs):
    raise socket.gaierror("not found")


def private_resolver(host, port, **kwargs):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 0))]


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

    def test_rejects_private_network_targets(self):
        issues = validate_urls("http://localhost/test\nhttps://internal.example/test", resolver=private_resolver)
        self.assertEqual(len(issues), 2)
        self.assertIn("localhost", issues[0].message)
        self.assertIn("private", issues[1].message)

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
