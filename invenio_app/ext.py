# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

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
        for k in dir(config):
            if any([k.startswith(prefix) for prefix in config_apps]):
                app.config.setdefault(k, getattr(config, k))
