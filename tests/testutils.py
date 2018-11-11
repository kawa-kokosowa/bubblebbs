import unittest

from bubblebbs import app
from bubblebbs import config


# FIXME: why does this have setUpClass and setUp?
class DatabaseTest(unittest.TestCase):

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


