import unittest

from legal_style_validator import validate_legal_style


class LegalStyleValidatorTests(unittest.TestCase):
    def test_flags_missing_legal_italics(self):
        markdown = """See Smith v. Jones.
The source is available at https://example.com.
Smith, supra note 4.
Jones, infra note 7.
But see Brown v. Board.
Id. at 4.
Ibid. at 5.
see, e.g., Green v. White.
"""
        issues = validate_legal_style(markdown)
        self.assertEqual(
            [issue.term for issue in issues],
            [
                "See",
                "available at",
                "supra/infra",
                "note",
                "supra/infra",
                "note",
                "See",
                "Id./Ibid.",
                "Id./Ibid.",
                "See",
            ],
        )

    def test_accepts_markdown_italics(self):
        markdown = """_See_ Smith v. Jones.
The source is _available at_ https://example.com.
Smith, _supra_ _note_ 4.
Jones, *infra* *note* 7.
_But see_ Brown v. Board.
_Id._ at 4.
*Ibid.* at 5.
_see, e.g.,_ Green v. White.
"""
        self.assertEqual(validate_legal_style(markdown), [])

    def test_accepts_larger_italic_span(self):
        markdown = "Smith, _supra note 4_; _See also_ Jones; _IBID. at 9_."
        self.assertEqual(validate_legal_style(markdown), [])

    def test_all_signal_rules_are_case_insensitive(self):
        markdown = """see Smith.
SEE ALSO Jones.
bUt SeE Brown.
ID. at 4.
iBiD. at 5.
SUPRA NOTE 6.
INFRA NOTE 7.
AVAILABLE AT https://example.com.
"""
        terms = [issue.term for issue in validate_legal_style(markdown)]
        self.assertEqual(
            terms,
            [
                "See",
                "See",
                "See",
                "Id./Ibid.",
                "Id./Ibid.",
                "supra/infra",
                "note",
                "supra/infra",
                "note",
                "available at",
            ],
        )

    def test_compound_see_signal_requires_whole_phrase_italics(self):
        issues = validate_legal_style("_See_, e.g., Smith v. Jones.")
        self.assertEqual([issue.term for issue in issues], ["See"])
        self.assertEqual(validate_legal_style("_See, e.g.,_ Smith v. Jones."), [])

    def test_lowercase_prose_see_is_checked(self):
        issues = validate_legal_style("Please see the appendix.")
        self.assertEqual([issue.term for issue in issues], ["See"])
        self.assertEqual(validate_legal_style("Please _see_ the appendix."), [])

    def test_ignores_code(self):
        markdown = """`See Id. supra note 4 available at`
```
see id. supra note 4 available at
```
"""
        self.assertEqual(validate_legal_style(markdown), [])


if __name__ == "__main__":
    unittest.main()
