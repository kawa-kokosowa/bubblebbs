# TODO: CSRF Protection and validation
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, HiddenField, BooleanField
from wtforms.validators import DataRequired, Email
from flask_wtf.file import FileField, FileRequired
from werkzeug.utils import secure_filename


class CookieManagementForm(FlaskForm):
    """Form for managing cookie settings.

    """

    remember_name = BooleanField()
    stylesheet = StringField(
        'Stylesheet URL',
        render_kw={'placeholder': 'http://example.org/style.css'},
    )


class NewPostForm(FlaskForm):
    """Form for creating a new post.

    """

    name = StringField(
        'Name',
        render_kw={'placeholder': 'name#tripcode'},
    )
    message = TextAreaField('Message', validators=[DataRequired()])
    reply_to = HiddenField('reply_to')
    sage = BooleanField()


class TripMetaForm(FlaskForm):
    bio = TextAreaField('Message', validators=[DataRequired()])
    unhashed_tripcode = StringField(
        'Unhashed Tripcode',
        render_kw={'placeholder': 'tripcode'},
    )
