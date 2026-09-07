from markdown_formatter import format_markdown


def test_formats_unordered_lists_and_italics():
    source = (
        "* first\n"
        "+ second\n"
        "    * nested\n"
        "\n"
        "Use *italics*, **bold**, and ***both***.\n"
    )

    assert format_markdown(source) == (
        "- first\n"
        "- second\n"
        "    - nested\n"
        "\n"
        "Use _italics_, **bold**, and **_both_**.\n"
    )


def test_preserves_code_and_thematic_breaks():
    source = (
        "```md\n"
        "* untouched list\n"
        "*untouched italics*\n"
        "```\n"
        "\n"
        "* * *\n"
        "Use `*literal*` and *real*.\n"
    )

    assert format_markdown(source) == (
        "```md\n"
        "* untouched list\n"
        "*untouched italics*\n"
        "```\n"
        "\n"
        "* * *\n"
        "Use `*literal*` and _real_.\n"
    )


def test_preserves_existing_canonical_markup():
    source = "- item\nAlready _italic_ and **bold**.\n"

    assert format_markdown(source) == source
