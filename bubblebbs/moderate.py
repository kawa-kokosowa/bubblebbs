"""Much of this is directly from flask-admin's example..."""

import os
import string
import random

from flask import Flask, url_for, redirect, render_template, request
from flask.ext.sqlalchemy import SQLAlchemy
from wtforms import form, fields, validators
from flask.ext import admin, login
from flask.ext.admin.contrib import sqla
from flask.ext.admin import helpers, expose
from werkzeug.security import generate_password_hash, check_password_hash
from jinja2 import Markup

from . import models
from . import forms
from . import config


def ban_lookup(request):
    return (
        models.db.session.query(models.Ban)
        .filter(models.Ban.address == request.remote_addr).first()
    )


# Define login and registration forms (for flask-login)
class LoginForm(form.Form):
    login = fields.TextField(validators=[validators.required()])
    password = fields.PasswordField(validators=[validators.required()])

    def validate_login(self, field):
        user = self.get_user()

        if user is None:
            raise validators.ValidationError('Invalid user')

        # we're comparing the plaintext pw with the the hash from the db
        if not check_password_hash(user.password, self.password.data):
        # to compare plain text passwords use
        # if user.password != self.password.data:
            raise validators.ValidationError('Invalid password')

    def get_user(self):
        return models.db.session.query(models.User).filter_by(login=self.login.data).first()


class PasswordField(fields.TextField):

    def process_data(self, value):
        self.data = ''  # even if password is already set, don't show hash here
        # or else it will be double-hashed on save
        self.orig_hash = value

    def process_formdata(self, valuelist):
        value = ''
        if valuelist:
            value = valuelist[0]
        if value:
            self.data = generate_password_hash(value)
        else:
            self.data = self.orig_hash


# FIXME: when is this used?!
class RegistrationForm(form.Form):
    login = fields.TextField(validators=[validators.required()])
    email = fields.TextField()
    password = fields.PasswordField(validators=[validators.required()])

    def validate_login(self, field):
        if models.db.session.query(User).filter_by(login=self.login.data).count() > 0:
            raise validators.ValidationError('Duplicate username')


# Initialize flask-login
def init_login(app):
    login_manager = login.LoginManager()
    login_manager.init_app(app)

    # Create user loader function
    @login_manager.user_loader
    def load_user(user_id):
        return models.db.session.query(models.User).get(user_id)


# Create customized model view class
class MyModelView(sqla.ModelView):
    column_display_pk = True

    def is_accessible(self):
        return login.current_user.is_authenticated


class AdminUserModelView(MyModelView):
    form_overrides = dict(
        password=PasswordField,
    )
    form_widget_args = dict(
        password={
            'placeholder': 'Enter new password here to change password',
        },
    )


class ConfigView(MyModelView):
    form_columns = ['value']
    column_list = ['key', 'value']
    # how to disable create view..?


# Create customized index view class that handles login & registration
class MyAdminIndexView(admin.AdminIndexView):

    @expose('/')
    def index(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))
        return super(MyAdminIndexView, self).index()

    @expose('/login/', methods=('GET', 'POST'))
    def login_view(self):
        # handle user login
        form = LoginForm(request.form)
        if helpers.validate_form_on_submit(form):
            user = form.get_user()
            login.login_user(user)

        if login.current_user.is_authenticated:
            return redirect(url_for('.index'))
        link = '<p>Don\'t have an account? <a href="' + url_for('.register_view') + '">Click here to register.</a></p>'
        self._template_args['form'] = form
        self._template_args['link'] = link
        return super(MyAdminIndexView, self).index()

    # FIXME: what the heck is this?!
    @expose('/register/', methods=('GET', 'POST'))
    def register_view(self):
        form = RegistrationForm(request.form)
        if helpers.validate_form_on_submit(form):
            user = models.User()

            form.populate_obj(user)
            # we hash the users password to avoid saving it as plaintext in the db,
            # remove to use plain text:
            user.password = generate_password_hash(form.password.data)

            models.db.session.add(user)
            models.db.session.commit()

            login.login_user(user)
            return redirect(url_for('.index'))
        link = '<p>Already have an account? <a href="' + url_for('.login_view') + '">Click here to log in.</a></p>'
        self._template_args['form'] = form
        self._template_args['link'] = link
        return super(MyAdminIndexView, self).index()

    @expose('/logout/')
    def logout_view(self):
        login.logout_user()
        return redirect(url_for('.index'))


# TODO: config
def build_sample_db():
    """
    Populate a small db with some example entries.
    """

    # FIXME: this is a horrible way to check for database
    # considering people may not even use sqlite!!!!
    if not os.path.isfile('bubblebbs/test.db'):
        models.db.create_all()
        test_user = models.User(login="admin", password=generate_password_hash("admin"))
        models.db.session.add(test_user)
        key_pairs = [
            ('site_tagline', config.SITE_TAGLINE),
            ('site_title', config.SITE_TITLE),
            ('site_footer', config.SITE_FOOTER),
        ]
        for key, value in key_pairs:
            models.db.session.add(models.ConfigPair(key=key, value=value))

        models.db.session.commit()

    return
