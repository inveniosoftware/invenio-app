# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration."""

from __future__ import absolute_import, print_function

import pytest
from flask import Flask

from invenio_app.config import APP_DEFAULT_SECURE_HEADERS


@pytest.fixture()
def base_app():
    """Flask application fixture."""
    app_ = Flask('testapp')
    app_.config.update(
        SECRET_KEY='SECRET_KEY',
        TESTING=True,
    )
    app_.config['APP_DEFAULT_SECURE_HEADERS'] = APP_DEFAULT_SECURE_HEADERS
    app_.config['APP_DEFAULT_SECURE_HEADERS']['force_https'] = False
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
        )
        app.config['APP_DEFAULT_SECURE_HEADERS'] = APP_DEFAULT_SECURE_HEADERS
        app.config['APP_DEFAULT_SECURE_HEADERS']['force_https'] = False
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
