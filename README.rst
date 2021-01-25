About tgext.utils
=================

.. image:: https://travis-ci.org/TurboGears/tgext.utils.png?branch=master
    :target: https://travis-ci.org/TurboGears/tgext.utils

.. image:: https://coveralls.io/repos/TurboGears/tgext.utils/badge.png?branch=master
    :target: https://coveralls.io/r/TurboGears/tgext.utils?branch=master

.. image:: https://img.shields.io/pypi/v/tgext.utils.svg
   :target: https://pypi.python.org/pypi/tgext.utils

tgext.utils is a collection of utilities for the TurboGears2 web framework.

Installing
----------

tgext.utils can be installed from pypi::

    pip install tgext.utils

should just work for most of the users.

CSRF Protection
===============

``tgext.utils.csrf`` provides two decorators ``@csrf_token`` and ``@csrf_protect`` which
generate a CSRF token for inclusion in a form and check that the token is valid.

The user must apply ``@csrf_token`` decorator to the action that exposes the form,
and put an ``<input type="hidden">`` into the form with a ``request.csrf_token`` as
the value and ``_csrf_token`` as name:

The user also should register the ``CSRFConfigurationComponent`` in it's application configuration
and configure at least ``csrf.secret`` in the blueprint/ini file (uuid4 is a good choice)

.. code-block:: python

    @csrf_token
    @expose()
    def form(self):
        return '''
        <form method="POST" action="/post_form">
            <input type="hidden" name="_csrf_token" value="%s">
	    <input type="submit"/>
        </form>''' % request.csrf_token

The action that receives the form must have ``@csrf_protect`` decorator,
no particular action or check is required on this action:

.. code-block:: python

    @csrf_protect
    @expose()
    def post_form(self, **kwargs):
        return 'OK!'

The generated cookie uses HMAC with sha384, sessionid and a timestamp, so each request gets a different token.
A signed cookie is also used to follow the double submit guideline https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html#double-submit-cookie

.. warning::
   This impacts user experience and usability.
   You may find the browser's back button "takes the user to expired forms"
   You may get additional expiration issues when the user uses multiple tabs of their browser

.. warning::
    If you're stuck with ``TG<2.4`` then upgrading this package (after 0.0.4) requires some (little) additional configuration work

.. warning::
   To make the double submit cookie technique more effective, using ``HSTS`` is highly recommended

MetaTags
========

``tgext.utils.meta.metatags`` provides a convenient way to generate common meta tags
for a web page.

In ``lib/helpers.py`` add:

.. code-block:: python

    from tgext.utils.meta import metatags

Then in your pages:

.. code-block:: html+genshi

    ${h.metatags(title="pagetitle", description="Page Description", image="http://url/myimage.png")}

Slug
====

``tgext.utils.slug`` provides a way to generate slug for your page

to generate a slug use:

.. code-block:: python

    from tgext.utils.slug import slugify
    myslug = slugify(model_id, string_to_be_inserted_in_the_url)

to get the id from a slug use:

.. code-block:: python

    from tgext.utils.slug import slug2entityid
    slug2entityid(myslug)

Storage
=======

``tgext.utils.storage`` is a tool for storing files into /public dir in separated folders.

.. code-block:: python

    from tgext.utils.storage import store

    filename = store(ufile)  # ufile is an instance of cgi.FieldStorage

file is stored inside /public/storage/${uuid1} folder thus also accessible using internal tg file serving.


Changelog
=========

- v0.0.5

  CSRF module: improved csrf module, config as per tg 2.4+

- v0.0.4
  META module: xss prevention

- v0.0.3
  STORAGE module: implemented
  SLUG module: minor fix and documentation
