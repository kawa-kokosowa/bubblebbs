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

    def test_reference_links(self):
        """Test the insertion of @2 style post reference links."""

        # The raw post text we hope to turn into something correctly parsed
        with open('tests/parsing/reference_links_unparsed.txt') as f:
            test_links_message = f.read()

        # We feed the raw post text and hope it's correctly parsed
        with self.app.app_context():
            hopefully_nicely_linked = models.Post.reference_links(test_links_message, 42)

        # What the post text *should* be after parsing it
        with open('tests/parsing/reference_links_parsed.txt') as f:
            correctly_parsed_nicely_linked = f.read()

        assert hopefully_nicely_linked == correctly_parsed_nicely_linked
