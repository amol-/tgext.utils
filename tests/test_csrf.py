# -*- coding: utf-8 -*-
from tg import expose, TGController, MinimalApplicationConfigurator, request
from tg.configurator.components.session import SessionConfigurationComponent
import webtest
from tgext.utils.csrf import csrf_protect, csrf_token, CSRFConfigurationComponent
from unittest.mock import patch, Mock


class RootController(TGController):
    @csrf_token
    @expose()
    def index(self):
        return 'Hello World'

    @csrf_protect
    @expose()
    def post_form(self, **kwargs):
        return 'OK!'

    @csrf_token
    @expose()
    def form(self):
        return '''
        <form method="POST" action="/post_form">
            <input type="hidden" name="_csrf_token" value="%s">
        </form>''' % request.csrf_token


class SessionMocked:
    def save(self):
        pass
    _id = '123'

    def __getitem__(self, k):
        return getattr(self, k)

class TestWSGIMiddleware(object):
    @classmethod
    def setup_class(cls):
        config = MinimalApplicationConfigurator()
        config.update_blueprint({
            'root_controller': RootController(),
            'csrf.secret': 'MYSECRET',
        })
        config.register(CSRFConfigurationComponent)
        config.register(SessionConfigurationComponent)
        cls.wsgi_app = config.make_wsgi_app()

    def make_app(self, **options):
        return webtest.TestApp(self.wsgi_app)

    @patch('tg.session', SessionMocked())
    def test_token_is_set(self):
        app = self.make_app()
        app.get('/index')
        assert '_csrf_token' in app.cookies

    @patch('tg.session', SessionMocked())
    def test_token_is_validated(self):
        app = self.make_app()
        resp = app.get('/post_form', status=403)
        assert 'The form you submitted is invalid or has expired' in resp

    @patch('tg.session', SessionMocked())
    def test_cookie_alone_is_not_enough(self):
        app = self.make_app()
        app.get('/index')
        resp = app.get('/post_form', status=403)
        assert 'The form you submitted is invalid or has expired' in resp

    @patch('tg.session', SessionMocked())
    def test_cookie_and_form_pass_check(self):
        app = self.make_app()
        resp = app.get('/form')
        resp = resp.forms[0].submit()
        assert 'OK' in resp
