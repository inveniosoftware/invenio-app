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

"""Pytest configuration."""

from __future__ import absolute_import, print_function

import pytest
from flask import Flask


@pytest.fixture()
def base_app():
    """Flask application fixture."""
    app_ = Flask('testapp')
    app_.config.update(
        SECRET_KEY='SECRET_KEY',
        TESTING=True,
        APP_DEFAULT_SECURE_HEADERS=dict(
            force_https=False,
        )
    )
    return app_


@pytest.yield_fixture()
def app(base_app):
    """Flask application fixture."""
    with base_app.app_context():
        yield base_app


@pytest.fixture()
def wsgi_apps():
    """Wsgi app fixture."""
    from invenio_base.wsgi import create_wsgi_factory, wsgi_proxyfix
    from invenio_base.app import create_app_factory

    def _config(app, **kwargs):
        app.config.update(
            SECRET_KEY='SECRET_KEY',
            TESTING=True,
            APP_DEFAULT_SECURE_HEADERS=dict(
                force_https=False,
            )
        )
    # API
    create_api = create_app_factory(
        'invenio',
        config_loader=_config,
        wsgi_factory=wsgi_proxyfix(),
    )
    # UI
    create_ui = create_app_factory(
        'invenio',
        config_loader=_config,
        wsgi_factory=wsgi_proxyfix(),
    )
    # Combined
    create_app = create_app_factory(
        'invenio',
        config_loader=_config,
        wsgi_factory=wsgi_proxyfix(create_wsgi_factory({'/api': create_api})),
    )
    return create_app, create_ui, create_api
