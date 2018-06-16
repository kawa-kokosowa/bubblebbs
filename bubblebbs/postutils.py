"""Post-parsing utilities which do not interact with the database."""

import os
import copy
import datetime
from urllib.parse import urlparse

import Identicon
import bleach
from bs4 import BeautifulSoup
import markdown
from mdx_bleach.extension import BleachExtension
from mdx_unimoji import UnimojiExtension
from markdown.extensions.footnotes import FootnoteExtension
from markdown.extensions.smarty import SmartyExtension
from markdown.extensions.wikilinks import WikiLinkExtension


def parse_markdown(message: str, allow_all=False) -> str:
    """Parse a markdown document..."""

    timestamp = datetime.datetime.utcnow()
    slug_timestamp = str(timestamp).replace(' ', '').replace(':', '').replace('.', '')
    FootnoteExtension.get_separator = lambda x: slug_timestamp + '-'
    extensions = [
        SmartyExtension(
            smart_dashes=True,
            smart_quotes=True,
            smart_ellipses=True,
            substitutions={},
        ),
        UnimojiExtension(),  # FIXME: add in configurable emojis, etc.
        'markdown.extensions.nl2br',
        'markdown.extensions.footnotes',
        'markdown.extensions.toc',
        'markdown.extensions.def_list',
        'markdown.extensions.abbr',
        'markdown.extensions.fenced_code',
    ]
    # FIXME: review, pentest
    if not allow_all:
        bleach = BleachExtension(
            strip=True,
            tags=[
                'h2',
                'h3',
                'h4',
                'h5',
                'h6',
                'blockquote',
                'ul',
                'ol',
                'dl',
                'dt',
                'dd',
                'li',
                'code',
                'sup',
                'pre',
                'br',
                'a',
                'p',
                'em',
                'strong',
            ],
            attributes={
                '*': [],
                'h2': ['id'],
                'h3': ['id'],
                'h4': ['id'],
                'h5': ['id'],
                'h6': ['id'],
                'li': ['id'],
                'sup': ['id'],
                'a': ['href'],  # FIXME: can people be deceptive with this?
            },
            styles={},
            protocols=['http', 'https'],
        )
        extensions.append(bleach)


    md = markdown.Markdown(extensions=extensions)
    return md.convert(message)


def add_domains_to_link_texts(html_message: str) -> str:
    """Append domain in parenthese to all link texts.

    Changes links like this:

        <a href="http://example.org/picture.jpg">Pic</a>
        <a href="/contact-us">Contact</a>

    ... to links like this:

        <a href="http://example.org/picture.jpg">Pic (example.org)</a>
        <a href="/contact-us">Contact (internal link)</a>

    Arguments:
        html_message: The HTML which to replace link text.

    Return:
        The HTML message with the links replaced as described above.

    """

    soup = BeautifulSoup(html_message, 'html5lib')

    # find every link in the message which isn't a "reflink"
    # and append `(thedomain)` to the end of each's text
    for anchor in soup.find_all('a'):
        if (not anchor.has_attr('href')) or ('reflink' in anchor.attrs.get('class', [])):
            continue

        # Copy the tag, change its properties, and replace the original
        new_tag = copy.copy(anchor)
        href_parts = urlparse(anchor['href'])
        link_class = 'external-link' if href_parts.hostname else 'internal-link'
        new_tag['class'] = new_tag.get('class', []) + [link_class]
        domain = href_parts.hostname if href_parts.hostname else 'internal link'
        new_tag.string = '%s (%s)' % (anchor.string, domain)
        anchor.replace_with(new_tag)

    # Return, stripped of the erroneous fluff elements html5lib
    # likes to nest everything into
    return str(soup)[len('<html><head></head><body>'):-len('</body></html>')]


def ensure_identicon(tripcode: str) -> str:
    """Make sure tripcode has an associated identicon.

    The identicon is a file saved in static/identicons/
    with the filename matching the tripcode.

    If no such file exists it will be created.

    Returns:
        str: the path to the identicon.

    """

    from . import app  # FIXME: this is hacky
    directory_where_identicons_go = os.path.join(
        app.app.static_folder,
        'identicons',
    )
    if not os.path.exists(directory_where_identicons_go):
        os.makedirs(directory_where_identicons_go)

    path_where_identicon_should_be = os.path.join(
        directory_where_identicons_go,
        tripcode + '.png',
    )

    if not os.path.isfile(path_where_identicon_should_be):
        identicon = Identicon.render(tripcode)
        with open(path_where_identicon_should_be, 'wb') as f:
            f.write(identicon)

    return path_where_identicon_should_be
