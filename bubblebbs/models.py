# FIXME: primary key being avoided because you have to do
# some annoying copypaste code to get primary keys to show
import os
import re
import base64
import zlib
import pathlib
import datetime
from typing import Tuple, Union
from urllib.parse import urlparse
import urllib.parse

import scrypt
import markdown
from mdx_bleach.extension import BleachExtension
from markdown.extensions.footnotes import FootnoteExtension
from markdown.extensions.smarty import SmartyExtension
from markdown.extensions.wikilinks import WikiLinkExtension
from flask import request
from sqlalchemy.exc import (InvalidRequestError, IntegrityError)
from jinja2 import Markup
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

from . import config


db = SQLAlchemy()


class ErrorPageException(Exception):
    def __init__(self, format_docstring: dict = {}):
        self.message = self.__doc__.format(**format_docstring)
        super().__init__(self.message)
        self.http_status = self.HTTP_STATUS


class RemoteAddrIsBanned(ErrorPageException):
    """The remote address {address} attempted to perform an action
    it has been banned/prohibited from performing.

    Ban reason: {reason}

    """

    HTTP_STATUS = 420  # FIXME


class DuplicateMessage(ErrorPageException):
    """You tried to make a (duplicate) post that's already been
    made before. Please try to be more original.

    """

    HTTP_STATUS = 420  # FIXME


class TripMeta(db.Model):
    """Keeps track of tripcodes and postcount. Plus, if user
    proves they know unhashed version of tripcode they can
    set a Twitter URL, other links, a bio.

    """

    tripcode = db.Column(db.String(20), primary_key=True)
    post_count = db.Column(db.Integer, default=0, nullable=False)
    bio = db.Column(db.String(1000))
    bio_source = db.Column(db.String(400))

    @staticmethod
    def increase_post_count_or_create(tripcode: str):
        if tripcode:
            trip_meta = db.session.query(TripMeta).get(tripcode)
            if trip_meta:
                trip_meta.post_count += 1
            else:
                new_trip_meta = TripMeta(
                    tripcode=tripcode,
                    post_count=1,
                )
                db.session.add(new_trip_meta)
            db.session.commit()


class BannablePhrases(db.Model):
    phrase = db.Column(db.String(100), primary_key=True)


class FlaggedIps(db.Model):
    """Keeps track of which IPs have exhibited "bad behavior."

    `ip_address` is not unique so varieties
    of infractions can be recorded.

    """

    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(120), nullable=False)
    reason = db.Column(db.String(100))

    @classmethod
    def new(cls, ip_address_to_flag: str, flag_reason: str = None):
        db.session.add(cls(ip_address=ip_address_to_flag, reason=flag_reason))
        db.session.commit()
        db.session.flush()


# FIXME: bad schema...
# TODO: tags
class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    ip_address = db.Column(db.String(120), nullable=False)
    locked = db.Column(db.Boolean(), default=False, nullable=False)
    verified = db.Column(db.Boolean(), default=False, nullable=False)
    headline = db.Column(db.String(140))
    permasage = db.Column(db.Boolean(), default=False, nullable=False)
    tripcode = db.Column(db.String(64))
    message = db.Column(db.String(2000), nullable=False, unique=True)
    reply_to = db.Column(db.Integer, db.ForeignKey('posts.id'))
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    bumptime = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)

    # FIXME: rename to_dict() and use summary output not full output
    def __iter__(self):
        """Turn into dict with dict(post)"""
        for column in self.__table__.columns:
            yield column.name, getattr(self, column.name)

    # TODO, FIXME
    @staticmethod
    def extract_hashtags(message: str):
        pass

    @staticmethod
    def name_tripcode_matches_original_use(name: str, tripcode: str) -> bool:
        """Verify that this usage of `name` has the correct
        tripcode as when `name` was originally used.

        """

        first_post_using_name = (
            Post.query
            .filter(Post.name == name)
            .order_by(Post.bumptime.asc())
            .first()
        )
        return (not first_post_using_name) or first_post_using_name.tripcode == tripcode

    @staticmethod
    def reference_links(form) -> str:
        """Parse >>id links"""

        if not form.reply_to.data:
            return form.message.data

        message = form.message.data
        reply_to = int(form.reply_to.data)

        pattern = re.compile('\>\>([0-9]+)')
        message_with_links = pattern.sub(
            r'<a href="/threads/%d#\1">&gt;&gt;\1</a>' % reply_to,
            message,
        )
        return message_with_links

    # FIXME: dangerous because untested for vulns
    @staticmethod
    def parse_markdown(timestamp: str, message: str) -> str:
        # FIXME: review, pentest
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
        slug_timestamp = str(timestamp).replace(' ', '').replace(':', '').replace('.', '')
        FootnoteExtension.get_separator = lambda x: slug_timestamp + '-'
        md = markdown.Markdown(
            extensions=[
                bleach,
                SmartyExtension(
                    smart_dashes=True,
                    smart_quotes=True,
                    smart_ellipses=True,
                    substitutions={},
                ),
                'markdown.extensions.nl2br',
                'markdown.extensions.footnotes',
                'markdown.extensions.toc',
                'markdown.extensions.def_list',
                'markdown.extensions.abbr',
                'markdown.extensions.fenced_code',
            ],
        )
        return md.convert(message)

    # FIXME: what if passed a name which contains no tripcode?
    @staticmethod
    def make_tripcode(form) -> Tuple[str, str]:
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
        if not (form.name.data and '#' in form.name.data[:-1]):
            return form.name.data, None

        name, unhashed_tripcode = form.name.data.split('#', 1)

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

    @staticmethod
    def tip_link_stuff(tip_link: str) -> Tuple[Union[str, None], Union[str, None]]:
        if not tip_link:
            return None, None
        elif (not tip_link.startswith('http://')) or (not tip_link.startswith('https://')):
            tip_link = 'http://' + tip_link

        tip_domain = urlparse(tip_link).hostname if tip_link else None
        return tip_link, tip_domain

    @staticmethod
    def word_filter(message, flag_if_filtered=True):
        # Finally let's do some wordfiltering. Wordfilters are useful because
        # you can catch bad words and flag users that use them.
        message_before_filtering = message

        word_filters = db.session.query(WordFilter).all()
        for word_filter in word_filters:
            find = re.compile(r'\b' + re.escape(word_filter.find) + r'(ies\b|s\b|\b)', re.IGNORECASE)
            # NOTE: I make it upper because I think it's funnier this way,
            # plus indicative of wordfiltering happening.
            message = find.sub(word_filter.replace.upper(), message)

        if flag_if_filtered and (message_before_filtering != message):
            FlaggedIps.new(request.remote_addr, 'word filter')

        return message

    @staticmethod
    def bannable_phrases(message: str):
        # Check if any banned phrases are in this text, and if so,
        # ban this user and don't make post!
        bannable_phrases = db.session.query(BannablePhrases).all()
        for phrase in bannable_phrases:
            if phrase.phrase in message:
                FlaggedIps.new(request.remote_addr, 'bannable phrase')
                Ban.new(request.remote_addr, 'bannable phrase: ' + phrase.phrase)

                raise RemoteAddrIsBanned(
                    format_docstring={
                        'address': request.remote_addr,
                        'reason': phrase.phrase,
                    },
                )

    @staticmethod
    def set_bump(form, reply_to, timestamp):
        if reply_to and not form.sage.data:
            original = db.session.query(Post).get(reply_to)
            if not original.permasage:
                original.bumptime = timestamp
                db.session.commit()

    @classmethod
    def mutate_message(cls, form, timestamp):
        """Change the message in various ways before saving to DB."""

        message = cls.reference_links(form)
        message = cls.parse_markdown(timestamp, message)
        message = cls.word_filter(message)
        return message

    @classmethod
    def get_headline(cls, message: str):
        message_parts = message.split('\n', 1)
        if len(message_parts) == 1:
            return None
        else:
            headline = message_parts[0]

        headline = cls.word_filter(headline, False)
        cleaned_headline = re.sub(r'<.*?>', '', headline)
        if cleaned_headline:
            return cleaned_headline.strip()
        else:
            return None

    # TODO: rename since now needs request for IP address
    @classmethod
    def from_form(cls, form):
        """Create and return a Post.

        The form may be a reply or a new post.

        Returns:
            Post: ...

        """

        # First the things which woudl prevent the post from being made
        Ban.ban_check(request.remote_addr)
        cls.bannable_phrases(form.message.data)

        reply_to = int(form.reply_to.data) if form.reply_to.data else None
        if reply_to and db.session.query(Post).get(reply_to).locked:
            raise Exception('This thread is locked. You cannot reply.')

        # FIXME: should sanitize first?
        # Prepare info for saving to DB
        headline = cls.get_headline(form.message.data)
        name, tripcode = cls.make_tripcode(form)
        matches_original_use = cls.name_tripcode_matches_original_use(name, tripcode)
        verified = matches_original_use
        if not verified:
            FlaggedIps.new(request.remote_addr, 'unoriginal usage of name (considering tripcode)')

        timestamp = datetime.datetime.utcnow()
        message = cls.mutate_message(form, timestamp)

        # Save!
        new_post = cls(
            name=name,
            headline=headline,
            tripcode=tripcode,
            timestamp=timestamp,
            message=message,
            verified=verified,
            reply_to=reply_to,
            ip_address=request.remote_addr,
        )
        # NOTE: this block with the flush and rollback seems like
        # high potential for breaking everything when high traffic?
        try:
            db.session.add(new_post)
            db.session.commit()
            db.session.flush()
        except (InvalidRequestError, IntegrityError) as e:
            db.session.rollback()
            raise DuplicateMessage()

        # TODO: after save method?
        TripMeta.increase_post_count_or_create(tripcode)
        cls.set_bump(form, reply_to, timestamp)

        return new_post


class Page(db.Model):
    __tablename__ = 'pages'
    slug = db.Column(db.String(60), primary_key=True)
    title = db.Column(db.String(200))
    body = db.Column(db.String(1000))
    source = db.Column(db.String(700))

    @classmethod
    def from_form(cls, form):
        body = Post.parse_markdown('lol', form.source.data)
        return cls(body=body, slug=form.slug.data, source=form.body.data)


# Create user model.
# TODO: rename admin?
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    login = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120))
    password = db.Column(db.String(200))

    # Flask-Login integration
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id
    # Required for administrative interface
    def __unicode__(self):
        return self.username


class Ban(db.Model):
    """Admin can ban by address or network."""
    address = db.Column(db.String(100), primary_key=True)
    reason = db.Column(db.String(100))

    @classmethod
    def ban_check(cls, ip_address: str):
        ban = db.session.query(cls).get(ip_address)
        if ban:
            raise RemoteAddrIsBanned(format_docstring={'address': ban.address, 'reason': ban.reason})

    @classmethod
    def from_form(cls, form):
        new_ban = cls(
            address=form.address.data,
            reason=form.reason.data,
        )
        db.session.add(new_ban)
        db.session.commit()

        return new_ban

    @classmethod
    def new(cls, ip_address_to_ban: str, ban_reason: str = None) -> bool:
        try:
            db.session.add(cls(address=ip_address_to_ban, reason=ban_reason))
            db.session.commit()
            db.session.flush()
            return True
        except IntegrityError:
            db.session.rollback()
            return False


class BlotterEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(250))
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)


class ConfigPair(db.Model):
    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.String(1000), nullable=False)


class WordFilter(db.Model):
    find = db.Column(db.String(100), primary_key=True)
    replace = db.Column(db.String(1000), nullable=False)  # can be html
