# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio App configuration.

`Invenio-App` is partially overwriting default configuration of `Limiter` and
`Talisman` applications.
You can find below more details about which configuration are set.

For more information, please also see
`Flask-Limiter <https://flask-limiter.readthedocs.io/en/stable/>`_ and
`Flask-Talisman <https://github.com/GoogleCloudPlatform/flask-talisman/>`__
websites.
"""

RATELIMIT_DEFAULT = '5000/hour'
"""Default rate limit.

.. note:: Overwrite
   Flask-Limiter <https://flask-limiter.readthedocs.io/en/stable/>`_
   configuration.
"""

RATELIMIT_HEADERS_ENABLED = True
"""Enable rate limit headers. (Default: ``True``)

.. note:: Overwrite
   Flask-Limiter <https://flask-limiter.readthedocs.io/en/stable/>`_
   configuration.
"""

APP_ENABLE_SECURE_HEADERS = True
"""Enable Secure Headers. (Default: ``True``)

In case you want to disable completely `Talisman`, you can set to `False`.

Remember that, for development purpose, setting ```DEBUG = True``` is already
enough to disable any side effects such as force ``https``.

.. note::
    `W3C
    <https://www.w3.org/TR/CSP2/>`_
"""

APP_DEFAULT_SECURE_HEADERS = {
    'force_https': True,
    'force_https_permanent': False,
    'force_file_save': False,
    'frame_options': 'sameorigin',
    'frame_options_allow_from': None,
    'strict_transport_security': True,
    'strict_transport_security_preload': False,
    'strict_transport_security_max_age': 31556926,  # One year in seconds
    'strict_transport_security_include_subdomains': True,
    'content_security_policy': {
        'default-src': ["'self'"],
        'object-src': ["'none'"]
    },
    'content_security_policy_report_uri': None,
    'content_security_policy_report_only': False,
    'session_cookie_secure': True,
    'session_cookie_http_only': True
}
"""Talisman default Secure Headers configuration.

As default, invenio assumes that HTTPS is enabled.
If you are not using SSL, then remember to disable the `force_https` and
`session_cookie_secure` configuration options related to HTTPS.

Please note that, as default `Talisman` behaviour, if Flask `DEBUG` mode is on,
then also many security barriers are automatically switched off
(e.g. `force_https` and `session_cookie_secure`).

.. note:: Overwrite
    `Flask-Talisman
    <https://github.com/GoogleCloudPlatform/flask-talisman>`_ configuration.

.. code-block:: python

    from flask import Flask
    from flask_talisman import Talisman

    app = Flask(__name__)
    app.config.update(
        SECRET_KEY='SECRET_KEY'
    )
    talisman = Talisman(app)

    @app.route('/defenders')
    @talisman(frame_options_allow_from='*')
    def defenders():
        \"\"\"Override policies for the specific view.\"\"\"
        return 'Jessica Jones'
"""

APP_ALLOWED_HOSTS = None
"""A list of host/domain names that can be served.

This is a security measure to prevent HTTP Host header attacks, which are
possible even under many seemingly-safe web server configurations.

By default all hosts are allowed. Values in this list can be fully qualified
names (e.g. 'www.example.com'). The validation only applies to
``request.host``.

In addition to this configuration variable, you should make sure that your
web server does not route requests to the application with an invalid Host
header.
"""

APP_HEALTH_BLUEPRINT_ENABLED = True
"""Enable the ping (healthcheck) blueprint. (Default: ``False``)
"""
