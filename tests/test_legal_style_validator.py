import unittest

from legal_style_validator import validate_legal_style


class LegalStyleValidatorTests(unittest.TestCase):
    def test_flags_missing_legal_italics(self):
        markdown = """See Smith v. Jones.
The source is available at https://example.com.
Smith, supra note 4.
Jones, infra note 7.
But see Brown v. Board.
"""
        issues = validate_legal_style(markdown)
        self.assertEqual(
            [issue.term for issue in issues],
            ["See", "available at", "supra/infra", "note", "supra/infra", "note", "See"],
        )

    def test_accepts_markdown_italics(self):
        markdown = """_See_ Smith v. Jones.
The source is _available at_ https://example.com.
Smith, _supra_ _note_ 4.
Jones, *infra* *note* 7.
_But see_ Brown v. Board.
"""
        self.assertEqual(validate_legal_style(markdown), [])

    def test_accepts_larger_italic_span(self):
        markdown = "Smith, _supra note 4_; _See also_ Jones."
        self.assertEqual(validate_legal_style(markdown), [])

    def test_ignores_code_and_lowercase_prose_see(self):
        markdown = """Please see the appendix.
`See supra note 4 available at`
```
See supra note 4 available at
```
"""
        self.assertEqual(validate_legal_style(markdown), [])


if __name__ == "__main__":
    unittest.main()
