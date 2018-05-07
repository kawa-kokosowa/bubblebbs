import os

SECRET_KEY = os.environ.get('BBBS_SECRET_KEY', 'PLEASE CHANGE ME')
SQLALCHEMY_DATABASE_URI = os.environ.get('BBBS_DB_STRING', 'sqlite:///test.db')
SITE_TAGLINE = os.environ.get('BBBS_SITE_TAGLINE', 'some tagline')
SITE_TITLE = os.environ.get('BBBS_SITE_TAGLINE', 'super title')
SITE_FOOTER = os.environ.get(
    'BBBS_SITE_FOOTER',
    '<a href="https://github.com/lily-mayfield/bubblebbs">Powered by BubbleBBS</a>',
)
RATELIMIT_STORAGE_URL = 'redis://localhost:6379/1'
