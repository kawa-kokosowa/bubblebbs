import os


BEHIND_REVERSE_PROXY = bool(os.environ.get('BBBS_BEHIND_REVERSE_PROXY', False))

POSTS_PER_PAGE = 25
TEMPLATES_AUTO_RELOAD = True

RECAPTCHA_ENABLED = os.environ.get('BBBS_RECAPTCHA_ENABLED', False)
RECAPTCHA_SITE_KEY = os.environ.get('BBBS_RECAPTCHA_SITE_KEY', 'CHANGEGME')
RECAPTCHA_SECRET_KEY = os.environ.get('BBS_RECAPTCHA_SECRET_KEY', 'CHANGEME')

SECRET_KEY = os.environ.get('BBBS_SECRET_KEY', 'PLEASE CHANGE ME')
SECRET_SALT = os.environ.get('BBBS_SECRET_SALT', 'CHANGEME')
SQLALCHEMY_DATABASE_URI = os.environ.get('BBBS_DB_STRING', 'sqlite:///test.db')

SITE_TAGLINE = os.environ.get('BBBS_SITE_TAGLINE', 'some tagline')
SITE_TITLE = os.environ.get('BBBS_SITE_TAGLINE', 'super title')
SITE_FOOTER = os.environ.get(
    'BBBS_SITE_FOOTER',
    '<a href="https://github.com/kawa-kokosowa/bubblebbs">Powered by BubbleBBS</a>',
)

RATELIMIT_STORAGE_URL = os.environ.get('BBBS_RATELIMIT_STORAGE_URL', 'redis://localhost:6379/1')
RATELIMIT_DEFAULT = "400 per day, 100 per hour"
RATELIMIT_ENABLED = True
RATELIMIT_LIST_THREADS = "20 per minute, 1 per second"
RATELIMIT_VIEW_SPECIFIC_POST = "20 per minute, 1 per second"
RATELIMIT_NEW_REPLY = "20 per hour, 1 per second, 2 per minute"
RATELIMIT_VIEW_TRIP_META = "50 per hour, 15 per minute"
RATELIMIT_EDIT_TRIP_META = "60 per hour, 1 per second, 4 per minute"
RATELIMIT_MANAGE_COOKIE = '60 per hour, 1 per second, 7 per minute'
RATELIMIT_CREATE_THREAD = '7 per hour, 1 per minute'
RATELIMIT_NEW_THREAD_FORM = '60 per hour, 1 per second'
