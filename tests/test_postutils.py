from bubblebbs import postutils
from bubblebbs import models

from . import testutils


class TestDatabasePostUtils(testutils.DatabaseTest):
    """Test post utilities which require a database connection."""

    def test_reference_links(self):
        """Test the insertion of @2 style post reference links."""

        # The raw post text we hope to turn into something correctly parsed
        with open('tests/parsing/reference_links_unparsed.txt') as f:
            test_links_message = f.read()

        # We feed the raw post text and hope it's correctly parsed
        with self.app.app_context():
            hopefully_nicely_linked = postutils.reference_links(models.Post, test_links_message, 42)

        # What the post text *should* be after parsing it
        with open('tests/parsing/reference_links_parsed.txt') as f:
            correctly_parsed_nicely_linked = f.read()

        assert hopefully_nicely_linked == correctly_parsed_nicely_linked


def test_make_tripcode():
    assert ('bleh', 'CWj74YsG7iMjTMMxPvhZpA--') == postutils.make_tripcode('bleh#lol')


def test_parse_markdown():

    # The raw post text we hope to turn into something correctly parsed
    with open('tests/parsing/parse_markdown_unparsed.txt') as f:
        markdown_to_parse = f.read()

    # What the post text *should* be after parsing it
    with open('tests/parsing/parse_markdown_parsed.txt') as f:
        correct_html_output = f.read()

    # Hopefully this parses correctly!
    # FIXME: using strip() on correct_html_output is bad!
    hopefully_correct_output = postutils.parse_markdown(markdown_to_parse, unique_slug='cats')
    assert hopefully_correct_output == correct_html_output.strip()


def test_add_domains_to_link_texts():

    # The raw post text we hope to turn into something correctly parsed
    with open('tests/parsing/add_domains_to_link_texts_unparsed.txt') as f:
        message_to_parse = f.read()

    # What the post text *should* be after parsing it
    with open('tests/parsing/add_domains_to_link_texts_parsed.txt') as f:
        correctly_parsed_message = f.read()

    # Hoping this parses correctly using the raw post text!
    hopefully_correctly_parsed = postutils.add_domains_to_link_texts(message_to_parse)
    assert hopefully_correctly_parsed == correctly_parsed_message
