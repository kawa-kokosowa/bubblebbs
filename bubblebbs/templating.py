"""Code specifically used by Jinja for rendering HTML
from Jinja templates.

"""

# TODO: move all the model stuff that's templating into here
import re
import os
import copy
import datetime
import base64
from urllib.parse import urlparse
from typing import Tuple

from flask import request
from bs4 import BeautifulSoup
import scrypt
import Identicon
import bleach
import markdown
from mdx_bleach.extension import BleachExtension
from mdx_unimoji import UnimojiExtension
from markdown.extensions.footnotes import FootnoteExtension
from markdown.extensions.smarty import SmartyExtension
from markdown.extensions.wikilinks import WikiLinkExtension

from . import models
from . import config


TRUNCATE_LENGTH = 140


def reference_links(post_model, message: str, reply_to: int = None) -> str:
    """Parse @id links.

    Explicitly avoids generating links within links.

    """

    def replace(match):
        at_number = int(match.group(1))

        # Construct the link based on determining if this is
        # a reference to a thread or if it's a reference to a reply
        post_referenced = post_model.query.get(at_number)
        if not post_referenced:
            valid = False
        elif post_referenced.reply_to:
            link = '%d#%d' % (post_referenced.reply_to, post_referenced.id)
            valid = True
        else:
            link = str(post_referenced.id)
            valid = True

        if valid:
            return '<a href="/threads/%s" class="reflink">@%d</a>' % (link, at_number)
        else:
            return '<span class="reflink reflink-invalid">@%d</span>' % at_number

    soup = BeautifulSoup(message, 'html.parser')
    at_link_pattern = re.compile(r'@(\d+)')
    for text_match in soup.find_all(text=True):
        if re.search(at_link_pattern, text_match) and text_match.parent.name != 'a':
            new_text = re.sub(at_link_pattern, replace, text_match)
            text_match.replace_with(new_text)

    return soup.prettify(formatter=None)


# FIXME: what if passed a name which contains no tripcode?
def make_tripcode(form_name: str) -> Tuple[str, str]:
    """Create a tripcode from the name field of a post.

    Returns:
        tuple: A two-element tuple containing (in the order of):
            name without tripcode, tripcode.

    Warning:
        Must have `this#format` or it will raise an exception
        related to unpacking.

    """

    # A valid tripcode is a name field containing an octothorpe
    # that isn't the last character.
    if not (form_name and '#' in form_name[:-1]):
        return form_name, None

    name, unhashed_tripcode = form_name.split('#', 1)

    # Create the salt
    if len(name) % 2 == 0:
        salt = name + config.SECRET_SALT
    else:
        salt = config.SECRET_SALT + name

    tripcode = str(
        base64.b64encode(
            scrypt.hash(
                name + config.SECRET_KEY + unhashed_tripcode,
                salt,
                buflen=16,
            ),
        ),
    )[2:-1].replace('/', '.').replace('+', '_').replace('=', '-')
    return name, tripcode


def youtube_link_to_embed(markdown_message):
    """

    Only replaces one link tops.

    """

    replacement = r'<iframe allow="autoplay; encrypted-media" allowfullscreen frameborder="0" height="270" src="https://www.youtube.com/embed/\1" width="480"></iframe>'
    regex = r"(?:https:\/\/)?(?:www\.)?(?:youtube\.com|youtu\.be)\/(?:watch\?v=)?(.+)"
    return re.sub(regex, replacement, markdown_message, 1)


def parse_markdown(message: str, allow_all=False, unique_slug=None) -> str:
    """Parse a markdown document to HTML with python-markdown.

    Configures/uses various python-markdown extensions.

    Arguments:
        message: The markdown message to parse into html.
        allow_all: Don't use bleach, don't sanitize.
        unique_slug: When specified overrides the timestamp slug
            which is prepended to all HTML element id attribute values.

    Returns:
        The HTML resulted from parsing the markdown with
        python-markdown + various extensions for it.

    """

    # Generate a url-friendly timestamp to avoid creating
    # the same id twice across two or more posts.
    # FIXME: Implement for TOC
    if unique_slug is None:
        timestamp = datetime.datetime.utcnow()
        # FIXME: surely there's a better way to url-ify this...
        unique_slug = str(timestamp).replace(' ', '').replace(':', '').replace('.', '')
    FootnoteExtension.get_separator = lambda x: unique_slug + '-'

    # Configure the rest of the extensions!
    extensions = [
        SmartyExtension(
            smart_dashes=True,
            smart_quotes=True,
            smart_ellipses=True,
            substitutions={},
        ),
        UnimojiExtension(),  # FIXME: add in configurable emojis, etc.
        'mdx_linkify',
        'markdown.extensions.nl2br',
        'markdown.extensions.footnotes',
        'markdown.extensions.toc',
        'markdown.extensions.def_list',
        'markdown.extensions.abbr',
        'markdown.extensions.fenced_code',
    ]
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
		'iframe',
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
                'a': ['href', 'class'],
		'iframe': ['allow', 'width', 'height', 'src', 'frameborder', 'allowfullscreen'],
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

    soup = BeautifulSoup(html_message, 'html.parser')

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

    return soup.prettify(formatter=None)


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
        app.blueprint.static_folder,
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


def truncate(some_string: str, length: int = None):
    length = length if length else TRUNCATE_LENGTH
    if len(some_string) > length:
        return some_string[:length] + '…'
    else:
        return some_string


# TODO: no need for headline field...
# Strip HTML...
def post_summary(post, length=None):
    return truncate(BeautifulSoup(message_to_html(post.message), 'html.parser').find().get_text().strip().split('\n')[0], length=length)


def get_stylesheet():
    return request.cookies.get('stylesheet_url')


def get_pages():
    return models.db.session.query(models.Page).all()


def get_blotter_entries():
    return models.BlotterEntry.query.order_by(models.BlotterEntry.id.desc()).all()


# FIXME: rename to "contrast text" or something
# TODO: the brightness factor...
def complementary_color(my_hex):
    """Returns maximal contrast color to provided.

    Example:
    >>>complementaryColor('FFFFFF')
    '000000'

    """

    if my_hex[0] == '#':
        my_hex = my_hex[1:]

    my_hex_number = int(my_hex, 16)
    absolute_grey = int('ffffff', 16) / 2

    if my_hex_number > absolute_grey:
        return '000000'
    elif my_hex_number == absolute_grey:
        return '000000'
    else:
        return 'ffffff'


def since_bumptime(bumptime, thread=None, reply=None):
    total_seconds = int((bumptime.now() - bumptime).total_seconds())
    days, seconds = divmod(total_seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    pairs = (
        (days, 'Day'),
        (hours, 'Hour'),
        (minutes, 'Minute'),
        (seconds, 'Second'),
    )
    parts = []
    for value, unit_singular in pairs:
        if value:
            output = '%d %s' % (value, unit_singular)
            if value > 1:
                output += 's'
            parts.append(output)

    if parts:
        very_readable = parts[0]
    else:
        very_readable = 'now'

    datetime_w3c_spec = str(bumptime)[:-3]

    if thread:
        permalink = '<a href="/threads/{permalink}">{parts} ago</a>'.format(
            permalink='%d#%d' % (thread, reply) if reply else thread,
            parts=very_readable,
        )
    elif reply:
        raise Exception('heck no!')
    else:
        permalink = very_readable + ' ago'

    return '''
    <time datetime="{bumptime}" title="{bumptime}">
    {permalink} 
    </time>
    '''.format(bumptime=datetime_w3c_spec, permalink=permalink)


def message_to_html(message: str, reply_to: int = None):
    """Take a post message (from database) that in its raw/markdown
    form and create the final HTML output for that post based on it.

    """

    message = youtube_link_to_embed(message)
    message = parse_markdown(message)
    message = reference_links(models.Post, message, reply_to)
    message = add_domains_to_link_texts(message)

    # If message gets filtered flag poster's IP
    message, was_filtered = models.WordFilter.replace_all(message)
    if was_filtered:
        models.FlaggedIps.new(request.remote_addr, 'word filter')

    return message


# FIXME: move to raw_message_to..
def mutate_message(form):
    """Change the message in various ways before saving to DB."""

    message = form.message.data
    message = templating.youtube_link_to_embed(message)
    message = templating.parse_markdown(message)
    message = templating.reference_links(cls, message, int(form.reply_to.data) if form.reply_to.data else None)
    message = templating.add_domains_to_link_texts(message)

    # If message gets filtered flag poster's IP
    message, was_filtered = models.WordFilter.replace_all(message)
    if was_filtered:
        models.FlaggedIps.new(request.remote_addr, 'word filter')

    return message


