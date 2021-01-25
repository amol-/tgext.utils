from __future__ import unicode_literals

import tg
from tg.decorators import before_validate
from tg.configurator import ConfigurationComponent, EnvironmentLoadedConfigurationAction
from tg.support.converters import asbool, asint

from datetime import datetime
import os
import hmac
import logging


def asbytes(obj):
    return obj.encode('ascii')

ENCODING = 'latin1'


def _csrf_error(reason):
    logging.warning('possible CSRF attack mitigated, details: %s', reason)
    tg.abort(403, 'The form you submitted is invalid or has expired: ' + reason)


class CSRFConfigurationComponent(ConfigurationComponent):
    """A component that will add CSRF protection to your forms"""
    id = 'csrf'

    def get_defaults(self):
        return {
            'csrf.enabled': True,
            'csrf.secret': None,
            'csrf.token_name': '_csrf_token',
            'csrf.expires': 60 * 10,
            'csrf.path': '/',  # cookie path
            'csrf.error_handler': _csrf_error,
        }
    def get_coercion(self):
        return {
            'csrf.enabled': asbool,
            'csrf.secret': asbytes,
            'csrf.expires': asint,
        }

    def on_bind(self, configurator):
        pass


def _get_conf():
    """
    Return CSRF configuration options.

    This function raises ``KeyError`` if configuration misses
    """
    conf = tg.config
    csrf_secret = conf['csrf.secret']
    csrf_token_name = conf['csrf.token_name']
    csrf_path = conf['csrf.path'].encode(ENCODING)
    cookie_expires = conf['csrf.expires']
    handler = conf['csrf.error_handler']
    return csrf_secret, csrf_token_name, csrf_path, cookie_expires, handler


def _generate_csrf_token():
    """
    Generate and set new CSRF token in cookie. The generated token is set to
    ``request.csrf_token`` attribute for easier access by other functions.
    """
    secret, token_name, path, expires, _ = _get_conf()
    session_id = tg.session['_id']
    tg.session.save()
    timestamp = str(datetime.utcnow().timestamp())
    digest = hmac.new(secret, (session_id + timestamp).encode('ascii'), digestmod='sha384').hexdigest()
    token = digest + ',' + timestamp
    tg.response.signed_cookie(token_name, token, secret.decode('ascii'),
                              path=path, max_age=expires)
    tg.request.csrf_token = token


def _validate_csrf(token):
    secret, token_name, path, expires, handler = _get_conf()
    session_id = tg.session['_id'] 
    digest, timestamp = token.split(',')
    if float(timestamp) < datetime.utcnow().timestamp() - expires:
        handler('expired')
    new_digest = hmac.new(secret, (session_id + timestamp).encode('ascii'), digestmod='sha384').hexdigest()
    if not hmac.compare_digest(digest, new_digest):
        handler('digest differs')


@before_validate
def csrf_token(remainder, params):
    """
    Create and set CSRF token in preparation for subsequent POST request. This
    decorator is used to set the token.
    It also sets the ``'Cache-Control'`` header in order to prevent caching of
    the page on which the token appears.

    The POST handler must use the :py:func:`~csrf_protect` decorator for the
    token to be used in any way.

    The token is available in the ``tg.request`` object as ``csrf_token``
    attribute::

        @csrf_token
        @expose('myapp.templates.put_token')
        def put_token_in_form():
            return dict(token=request.csrf_token)

    In a view, you can render this token as a hidden field inside the form. The
    hidden field must have the name specified in configuration ``csrf.token_name``,
    by default it is ``_csrf_token``::

        <form method="POST">
            <input type="hidden" name="_csrf_token" value="{{ token }}">
            ....
        </form>
    """
    _generate_csrf_token()
    # Pages with CSRF tokens should not be cached
    req = tg.request._current_obj()
    req.headers[str('Cache-Control')] = ('no-cache, max-age=0, '
                                         'must-revalidate, no-store')


@before_validate
def csrf_protect(remainder, params):
    """
    Perform CSRF protection checks. Performs checks to determine if submitted
    form data matches the token in the cookie. It is assumed that the GET
    request handler successfully set the token for the request and that the
    form was instrumented with a CSRF token field. Use the
    :py:func:`~csrf_token` decorator to do this.

    Generally, the handler does not need to do anything
    CSRF-protection-specific. All it needs is the decorator::

        @csrf_protect
        @expose()
        def protected_post_handler():
            return 'OK!'
    """
    req = tg.request._current_obj()

    secret, token_name, path, expires, handler = _get_conf()
    
    cookie_token = req.signed_cookie(token_name, secret=secret.decode('ascii'))
    if not cookie_token:
        handler('csrf cookie not present')

    form_token = req.args_params.get(token_name)
    if not form_token:
        handler('csrf input not present')

    if form_token != cookie_token:
        tg.response.delete_cookie(token_name, path=path)
        handler('cookie and input mismatch')

    _validate_csrf(form_token)
    
