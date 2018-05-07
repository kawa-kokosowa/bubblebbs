import os
import random

from flask import (
    Flask, redirect, render_template, url_for, send_from_directory, request, send_file, jsonify
)
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

from . import forms
from . import config
from . import models
from . import moderate


app = Flask(__name__)
app.config.from_object(config)


def config_db(key: str) -> str:
    """lol"""
    return models.ConfigPair.query.get(key).value


@app.route("/search-json", methods=['GET'])
def search_json():
    search_for_this_text = request.args.get('search')
    like_query = '%' + search_for_this_text + '%'
    posts = (
        models.Post.query.filter(
            models.Post.message.like(like_query),
        )
        .order_by(models.Post.bumptime.desc())
        .all()
    )
    return jsonify([dict(p) for p in posts])


@app.route("/", methods=['GET'])
def board_index():
    """View threads by bumptime.

    """

    # full text search
    search_for_this_text = request.args.get('search')
    if search_for_this_text:
        like_query = '%' + search_for_this_text + '%'
        posts = (
            models.Post.query.filter(
                models.Post.message.like(like_query),
            )
            .order_by(models.Post.bumptime.desc())
            .all()
        )
    else:
        posts = (
            models.Post.query.filter(models.Post.reply_to == None)
            .order_by(models.Post.bumptime.desc())
            .all()
        )

    for post in posts:
        reply_count = (
            models.Post.query
            .filter(models.Post.reply_to == post.id)
            .count()
        )
        post.reply_count = reply_count

    return render_template(
        'list.html',
        form=forms.NewPostForm(),
        posts=posts,
        blotter_entries=get_blotter_entries(),
    )


# FIXME: check if reply or not for error/404, else...
@app.route("/threads/<int:post_id>")
def view_specific_post(post_id: int):
    """View a thread by ID.

    """

    form = forms.NewPostForm()
    post = models.db.session.query(models.Post).get(post_id)
    if post.reply_to:
        return (
            render_template(
                'errors.html',
                errors=[
                    'Thread ID supplied is a reply id',
                    'Thread not found',
                ],
            ),
            404,
        )
    else:
        replies = (
            models.db.session.query(models.Post)
            .filter(models.Post.reply_to == post_id)
        )
        return render_template(
            'view-thread.html',
            form=form,
            post=post,
            replies=replies,
            blotter_entries=get_blotter_entries(),
        )


@app.route("/replies/new", methods=['POST'])
def new_reply():
    """Provide form for new thread on GET, create new thread on POST.

    """

    # FIXME: redundant
    # First check if IP banned
    ban = moderate.ban_lookup(request)
    if ban:
        ban_message = 'Your IP %s was banned: %s' % (ban.address, ban.reason)
        return render_template('errors.html', errors=[ban_message])

    reply_to = request.form.get('reply_to')
    form = forms.NewPostForm()

    if form.validate_on_submit():
        # FIXME: REDUNDANT!!!
        try:
            post = models.Post.from_form(form)
        except Exception as e:
            # FIXME: not 403 but some server-side error... should
            # catch various kinds of errors
            return render_template('errors.html', errors=[e]), 403

        # FIXME: if this is a new thread and the maximum number
        # of threads has been reached, delete the oldest thread
        # and its replies.

        return redirect(
            url_for(
                'view_specific_post',
                post_id=post.reply_to,
                _anchor=post.id,
            )
        )

    # FIXME: REDUNDANT!!!
    # TODO: earlier in process near other errors
    errors = []
    for field, field_errors in form.errors.items():
        field_name = getattr(form, field).label.text
        for error in field_errors:
            errors.append("%s: %s" % (field_name, error))
    return render_template('errors.html', errors=errors), 400


# FIXME must check if conflicting slug...
# what if making reply but reply is a comment?!
@app.route("/threads/new", methods=['GET', 'POST'])
def new_thread():
    """Provide form for new thread on GET, create new thread on POST.

    """

    if request.method == 'GET':
        return render_template('new-thread.html', form=forms.NewPostForm())
    elif request.method == 'POST':
        # First check if IP banned
        ban = moderate.ban_lookup(request)
        if ban:
            ban_message = 'Your IP %s was banned: %s' % (ban.address, ban.reason)
            return render_template('errors.html', errors=[ban_message])

        reply_to = request.form.get('reply_to')
        form = forms.NewPostForm()

        if form.validate_on_submit():
            try:
                post = models.Post.from_form(form)
            except Exception as e:
                # FIXME: not 403 but some server-side error... should
                # catch various kinds of errors
                return render_template('errors.html', errors=[e]), 403

            # FIXME: if this is a new thread and the maximum number
            # of threads has been reached, delete the oldest thread
            # and its replies.

            if post.reply_to:
                return redirect(
                    url_for(
                        'view_specific_post',
                        post_id=post.reply_to,
                        _anchor=post.id,
                    )
                )
            else:
                return redirect(
                    url_for(
                        'view_specific_post',
                        post_id=post.id,
                    )
                )

        # TODO: earlier in process near other errors
        errors = []
        for field, field_errors in form.errors.items():
            field_name = getattr(form, field).label.text
            for error in field_errors:
                errors.append("%s: %s" % (field_name, error))
        return render_template('errors.html', errors=errors), 400


def get_blotter_entries():
    return models.BlotterEntry.query.order_by(models.BlotterEntry.id.desc()).all()


# should go later in app factory...
with app.app_context():
    # Make it so can access config db from template
    app.jinja_env.globals.update(config_db=config_db)

    # Initialize flask-login
    moderate.init_login(app)

    # Create admin
    admin_ = Admin(app, 'Example: Auth', index_view=moderate.MyAdminIndexView(), base_template='my_master.html')

    # Add views
    admin_.add_view(moderate.AdminUserModelView(models.User, models.db.session))
    admin_.add_view(moderate.MyModelView(models.Post, models.db.session))
    admin_.add_view(moderate.MyModelView(models.Ban, models.db.session))
    admin_.add_view(moderate.MyModelView(models.BlotterEntry, models.db.session))
    admin_.add_view(moderate.ConfigView(models.ConfigPair, models.db.session))

    models.db.init_app(app)
    moderate.build_sample_db()
