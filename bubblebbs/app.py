# TODO: rename this view.py? put app factory in another file?
import os
import random
import datetime

from flask import (
    Flask, redirect, render_template, url_for, send_from_directory, request, send_file, jsonify, make_response
)
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from colorhash import ColorHash
from pymojihash.pymojihash import hash_to_emoji

from . import forms
from . import config
from . import models
from . import moderate
from . import templating


app = Flask(__name__)
app.config.from_object(config)
app.jinja_env.globals.update(
    since_bumptime=templating.since_bumptime,
    get_pages=templating.get_pages,
    hash_to_emoji=hash_to_emoji,
    color_hash=ColorHash,
    complementary_color=templating.complementary_color,
    get_blotter_entries=templating.get_blotter_entries,
    get_stylesheet=templating.get_stylesheet,
    recaptcha_site_key=config.RECAPTCHA_SITE_KEY,
)  # why not move this to templating?
# TODO: may add filter in future
app.jinja_env.filters = {
    **app.jinja_env.filters,
}
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["400 per day", "100 per hour"]
)


def config_db(key: str) -> str:
    """lol"""
    return models.ConfigPair.query.get(key).value


def validate_recaptcha():
    import requests
    verify_result = requests.post(
        'https://www.google.com/recaptcha/api/siteverify',
        data={
            'secret': '6Lc3-FkUAAAAAL-cl-zQA66aOFZD4ONGzQZdE-xh',
            'response': request.form['g-recaptcha-response'],
            'remoteip': request.remote_addr,
        },
    ).json()
    return verify_result['success'] == True


# NOTE: this currently isn't being used by anything!
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
@limiter.limit("30 per minute")
def list_threads():
    """View threads by bumptime in a list.

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
        reply_query = (
            models.Post.query
            .filter(models.Post.reply_to == post.id)
        )
        post.reply_count = reply_query.count()
        post.last_reply = reply_query.order_by(models.Post.bumptime.desc()).first()

    return render_template(
        'list.html',
        form=forms.NewPostForm(),
        posts=posts,
    )


# FIXME: check if reply or not for error/404, else...
@app.route("/threads/<int:post_id>")
@limiter.limit("45 per minute")
def view_specific_post(post_id: int):
    """View a thread by ID.

    """

    form = forms.NewPostForm(data=request.cookies if request.cookies.get('remember_name') else {})
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
        )


@app.route("/replies/new", methods=['POST'])
@limiter.limit("20 per hour")
def new_reply():
    """Provide form for new thread on GET, create new thread on POST.

    """

    if not validate_recaptcha():
        return render_template('errors.html', errors=['Captcha failed!'])

    reply_to = request.form.get('reply_to')
    form = forms.NewPostForm()

    if form.validate_on_submit():
        try:
            post = models.Post.from_form(form)
        except (models.RemoteAddrIsBanned, models.DuplicateMessage) as e:
            return render_template('errors.html', errors=[e]), e.http_status

        # FIXME: if this is a new thread and the maximum number
        # of threads has been reached, delete the oldest thread
        # and its replies.
        response = redirect(
            url_for(
                'view_specific_post',
                post_id=post.reply_to,
                _anchor=post.id,
            )
        )
        response = make_response(response)
        if form.name.data:
            response.set_cookie(
                'name',
                form.name.data,
                expires=datetime.datetime.now() + datetime.timedelta(days=30),
            )

        return response

    error_response = error_page_form_handler(form)
    if error_response:
        return error_response


@app.route('/pages/<slug>')
def view_page(slug: str):
    page = models.db.session.query(models.Page).get(slug)
    return render_template('page.html', page=page)


@app.route('/trip-meta/<path:tripcode>')
def view_trip_meta(tripcode: str):
    trip_meta = models.db.session.query(models.TripMeta).get(tripcode)
    posts_by_trip = (
        models.db.session.query(models.Post)
        .filter(models.Post.tripcode == tripcode)
        .order_by(models.Post.timestamp.desc())
        .all()
    )
    return render_template('view-trip-meta.html', trip_meta=trip_meta, posts=posts_by_trip)


@app.route('/trip-meta/<path:tripcode>/edit', methods=['POST', 'GET'])
@limiter.limit("45 per hour")
def edit_trip_meta(tripcode: str):
    trip_meta_form = forms.TripMetaForm()

    if request.method == 'GET':
        trip_meta_form.bio.data = models.db.session.query(models.TripMeta).get(tripcode).bio_source
        return render_template('edit-trip-meta.html', form=trip_meta_form, tripcode=tripcode)
    elif (request.method == 'POST'
          and trip_meta_form.validate_on_submit()
          and models.Post.make_tripcode('lol#' + trip_meta_form.unhashed_tripcode.data)[1] == tripcode):
        trip_meta = models.db.session.query(models.TripMeta).get(tripcode)
        trip_meta.bio_source = trip_meta_form.bio.data
        trip_meta.bio = models.Post.parse_markdown('', trip_meta_form.bio.data)
        models.db.session.commit()
        return redirect(url_for('view_trip_meta', tripcode=tripcode))
    else:
        raise Exception([models.Post.make_tripcode('lol#' + trip_meta_form.unhashed_tripcode.data), tripcode])


@app.route('/cookie', methods=['POST', 'GET'])
@limiter.limit("10 per hour")
def manage_cookie():
    cookie_form = forms.CookieManagementForm(data=request.cookies)

    if request.method == 'GET':
        return render_template('cookie.html', form=cookie_form)
    elif request.method == 'POST' and cookie_form.validate_on_submit():

        response = make_response(
            redirect(
                url_for(
                    'manage_cookie',
                ),
            ),
        )

        response.set_cookie(
            'stylesheet_url',
            cookie_form.stylesheet_url.data,
            expires=datetime.datetime.now() + datetime.timedelta(days=30),
        )
        response.set_cookie(
            'remember_name',
            'true' if cookie_form.remember_name.data else '',
            expires=datetime.datetime.now() + datetime.timedelta(days=30),
        )

        return response


def error_page_form_handler(form):
    errors = []
    for field, field_errors in form.errors.items():
        field_name = getattr(form, field).label.text
        for error in field_errors:
            errors.append("%s: %s" % (field_name, error))
    if errors:
        return render_template('errors.html', errors=errors), 400

    return None


# FIXME must check if conflicting slug...
# what if making reply but reply is a comment?!
@app.route("/threads/new", methods=['GET', 'POST'])
# FIXME: set back to 10
@limiter.limit("5 per hour")
def new_thread():
    """Provide form for new thread on GET, create new thread on POST.

    """

    if request.method == 'GET':
        new_thread_form = forms.NewPostForm(data=request.cookies if request.cookies.get('remember_name') else {})
        return render_template('new-thread.html', form=new_thread_form)
    elif request.method == 'POST':
        if not validate_recaptcha():
            return render_template('errors.html', errors=['Captcha failed!'])
        reply_to = request.form.get('reply_to')
        form = forms.NewPostForm()

        # TODO: why this if above
        if form.validate_on_submit():
            try:
                post = models.Post.from_form(form)
            except (models.RemoteAddrIsBanned, models.DuplicateMessage) as e:
                return render_template('errors.html', errors=[e]), e.http_status

            # FIXME: if this is a new thread and the maximum number
            # of threads has been reached, delete the oldest thread
            # and its replies.
            response = redirect(
                url_for(
                    'view_specific_post',
                    post_id=post.id,
                )
            )
        else:
            # TODO: earlier in process near other errors
            error_response = error_page_form_handler(form)
            if error_response:
                return error_response

        # FIXME
        response = make_response(response)
        if form.name.data:
            response.set_cookie(
                'name',
                form.name.data,
                expires=datetime.datetime.now() + datetime.timedelta(days=30),
            )

        return response


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
    admin_.add_view(moderate.BanView(models.Ban, models.db.session))
    admin_.add_view(moderate.MyModelView(models.BlotterEntry, models.db.session))
    admin_.add_view(moderate.MyModelView(models.FlaggedIps, models.db.session))
    admin_.add_view(moderate.PageModelView(models.Page, models.db.session))
    admin_.add_view(moderate.ConfigView(models.ConfigPair, models.db.session))
    admin_.add_view(moderate.WordFilterView(models.WordFilter, models.db.session))
    admin_.add_view(moderate.BannablePhraseView(models.BannablePhrases, models.db.session))

    models.db.init_app(app)
    moderate.build_sample_db()
