from bubblebbs import postutils


def test_add_domains_to_link_texts():
    message_to_parse = """
    Have you read <a href="http://www.example.org/somebook.pdf" class="heck">Some Book</a>?
    I thought it was similar to <a href="/downloads/anotherbook.pdf">Another
    Book</a>, which is hosted on this website.
    """.strip()
    parsed_message = """
    Have you read <a class="heck external-link" href="http://www.example.org/somebook.pdf">Some Book (www.example.org)</a>?
    I thought it was similar to <a class="internal-link" href="/downloads/anotherbook.pdf">Another
    Book (internal link)</a>, which is hosted on this website.
    """.strip()

    assert postutils.add_domains_to_link_texts(message_to_parse) == parsed_message
