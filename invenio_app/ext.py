# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio app extension."""

from __future__ import absolute_import, print_function

import pkg_resources
from flask_limiter import Limiter
from flask_limiter.util import get_ipaddr
from flask_talisman import Talisman

from . import config


class InvenioApp(object):
    """Invenio app extensions."""

    def __init__(self, app=None, **kwargs):
        r"""Extension initialization.

        :param app: An instance of :class:`~flask.Flask`.
        :param \**kwargs: Keyword arguments are passed to ``init_app`` method.
        """
        self.limiter = None
        self.talisman = None

        if app:
            self.init_app(app, **kwargs)

    def init_app(self, app, **kwargs):
        """Initialize application object.

        :param app: An instance of :class:`~flask.Flask`.
        """
        # Init the configuration
        self.init_config(app)
        # Enable Rate limiter
        self.limiter = Limiter(app, key_func=get_ipaddr)
        # Enable secure HTTP headers
        if app.config['APP_ENABLE_SECURE_HEADERS']:
            self.talisman = Talisman(
                app, **app.config.get('APP_DEFAULT_SECURE_HEADERS', {})
            )
        # Register self
        app.extensions['invenio-app'] = self

    def init_config(self, app):
        """Initialize configuration.

        :param app: An instance of :class:`~flask.Flask`.
        """
        config_apps = ['APP_', 'RATELIMIT_']
        flask_talisman_debug_mode = ["'unsafe-inline'"]
        for k in dir(config):
            if any([k.startswith(prefix) for prefix in config_apps]):
                app.config.setdefault(k, getattr(config, k))
        if app.config['DEBUG']:
            # set defaults if config overridden
            app.config.setdefault('APP_DEFAULT_SECURE_HEADERS', {})
            app.config['APP_DEFAULT_SECURE_HEADERS'].setdefault(
                'content_security_policy', {})
            app.config['APP_DEFAULT_SECURE_HEADERS'][
                'content_security_policy'].setdefault('default-src', [])
            # add default csp value when debug
            app.config['APP_DEFAULT_SECURE_HEADERS'][
                'content_security_policy']['default-src'] += \
                flask_talisman_debug_mode
