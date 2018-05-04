# FIXME: primary key being avoided because you have to do
# some annoying copypaste code to get primary keys to show
import os
import re
import base64
import pathlib
import datetime
from typing import Tuple, Union
from urllib.parse import urlparse

import scrypt
from jinja2 import Markup
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

from . import config


db = SQLAlchemy()


# FIXME: bad schema...
class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(120))
    name = db.Column(db.String(120))
    tripcode = db.Column(db.String(64))
    message = db.Column(db.String(2000), nullable=False)
    reply_to = db.Column(db.Integer, db.ForeignKey('posts.id'))
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    bumptime = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)

    @staticmethod
    def reference_links(message: str, thread_id: int) -> str:
        """Parse >>id links"""

        sanitized_message = str(Markup.escape(message))
        pattern = re.compile('\&gt\;\&gt\;([0-9]+)')
        message_with_links = pattern.sub(
            r'<a href="/threads/%d#\1">&gt;&gt;\1</a>' % thread_id,
            sanitized_message,
        )
        return message_with_links

    # FIXME: what if passed a name which contains no tripcode?
    @staticmethod
    def make_tripcode(name_and_tripcode: str) -> Tuple[str, str]:
        """Create a tripcode from the name field of a post.

        Returns:
            tuple: A two-element tuple containing (in the order of):
                name without tripcode, tripcode.

        Warning:
            Must have `this#format` or it will raise an exception
            related to unpacking.

        """

        name, unhashed_tripcode = name_and_tripcode.split('#', 1)
        tripcode = str(
            base64.b64encode(
                scrypt.hash(unhashed_tripcode, config.SECRET_KEY),
            ),
        )[2:22]
        return name, tripcode

    @staticmethod
    def tip_link_stuff(tip_link: str) -> Tuple[Union[str, None], Union[str, None]]:
        if not tip_link:
            return None, None
        elif (not tip_link.startswith('http://')) or (not tip_link.startswith('https://')):
            tip_link = 'http://' + tip_link

        tip_domain = urlparse(tip_link).hostname if tip_link else None
        return tip_link, tip_domain

    @classmethod
    def from_form(cls, form):
        """Create and return a Post.

        The form may be a reply or a new post.

        Returns:
            Post: ...

        """

        # A valid tripcode is a name field containing an octothorpe
        # that isn't the last character.
        if form.name.data and '#' in form.name.data[:-1]:
            name, tripcode = cls.make_tripcode(form.name.data)
        else:
            name = form.name.data
            tripcode = None

        # message link
        try:
            reply_to = int(form.reply_to.data)
            message = cls.reference_links(form.message.data, reply_to)
        except (ValueError, AttributeError) as e:
            reply_to = None
            message = form.message.data

        new_post = cls(
            name=name,
            tripcode=tripcode,
            message=message,
            reply_to=reply_to,
        )
        db.session.add(new_post)
        db.session.commit()

        if reply_to:
            original = db.session.query(Post).get(new_post.reply_to)
            original.bumptime = datetime.datetime.utcnow()
            db.session.commit()

        return new_post


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
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(100), unique=True)
    reason = db.Column(db.String(100))

    @classmethod
    def from_form(cls, form):
        new_ban = cls(
            address=form.address.data,
            reason=form.reason.data,
        )
        db.session.add(new_ban)
        db.session.commit()

        return new_ban


class BlotterEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(250))
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)


class ConfigPair(db.Model):
    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.String(1000))
