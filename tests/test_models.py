import os
import unittest

from bubblebbs import config
from bubblebbs import app
from bubblebbs import moderate
from bubblebbs import models


class TestPost(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config.SQLALCHEMY_DATABASE_URI = 'sqlite://'
        cls.app = app.create_app()
        cls.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'

    def setUp(self):
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['RATELIMIT_ENABLED'] = False
        self.test_app = self.app.test_client()
        app.limiter.enabled = False

        response = self.test_app.get('/')
        assert response.status_code == 200

        response = self.test_app.post('/threads/new', data={'name': 'uboa', 'message': 'lol'})
        assert response.status_code == 302

        response = self.test_app.post(
            '/replies/new',
            data={'name': 'uboa', 'message': 'heckers', 'reply_to': 1},
        )
        assert response.status_code == 302

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.app.config['SQLALCHEMY_DATABASE_URI'])

    # FIXME: needs test demo posts...
    def test_reference_links(self):
        test_links_message = '''
        guess what

        @2

        ur good

        @@asdf

        @1

        <a href="lol">@2</a>

        your @@ @ 33

        afsoiu wfkj wfe @1 ajs;lfkjasf@1

        @1f
        '''
        with self.app.app_context():
            hopefully_nicely_linked = models.Post.reference_links(test_links_message, 42)

        correctly_parsed_nicely_linked = '''
        guess what

        <a href="/threads/1#2" class="reflink">@2</a>

        ur good

        @@asdf

        <a href="lol">@2</a>

        <a href="/threads/1" class="reflink">@1</a>

        @dlasjf;lkjsd

        your @@ @ 33

        afsoiu wfkj wfe <a href="/threads/1#2" class="reflink">@2</a> ajs;lfkjasf<a href="/threads/1" class="reflink">@1</a>

        <a href="/threads/1" class="reflink">@1</a>f
        '''
        assert hopefully_nicely_linked == correctly_parsed_nicely_linked
