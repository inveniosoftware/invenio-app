# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

from __future__ import absolute_import, print_function

from flask import Flask
from werkzeug.http import parse_options_header

from invenio_app import InvenioApp


def test_rate_secure_headers(app):
    """Test Rate Limiter extension."""
    app.config['APP_ENABLE_SECURE_HEADERS'] = False
    # Initialize the app
    InvenioApp(app)
    assert 'talisman' not in app.extensions


def test_headers(app):
    """Test headers."""
    app.config['RATELIMIT_DEFAULT'] = '1/day'
    app.config['RATELIMIT_STORAGE_URL'] = 'memory://'
    ext = InvenioApp(app)

    for handler in app.logger.handlers:
        ext.limiter.logger.addHandler(handler)

    @app.route('/jessica_jones')
    def jessica_jones():
        return 'jessica jones'

    @app.route('/avengers')
    def avengers():
        return 'infinity war'

    with app.test_client() as client:
        res = client.get('/jessica_jones')
        assert res.status_code == 200
        assert res.headers['X-RateLimit-Limit'] == '1'
        assert res.headers['X-RateLimit-Remaining'] == '0'
        assert res.headers['X-RateLimit-Reset']

        res = client.get('/jessica_jones')
        assert res.status_code == 429
        assert res.headers['X-RateLimit-Limit']
        assert res.headers['X-RateLimit-Remaining']
        assert res.headers['X-RateLimit-Reset']

        res = client.get('/avengers')
        assert res.status_code == 200
        assert res.headers['X-Content-Security-Policy']
        assert res.headers['X-Content-Type-Options']
        assert res.headers['X-Frame-Options']
        assert res.headers['X-XSS-Protection']
        assert res.headers['X-RateLimit-Limit']
        assert res.headers['X-RateLimit-Remaining']
        assert res.headers['X-RateLimit-Reset']


def _normalize_csp_header(header):
    """Normalize a CSP header for consistent comparisons."""
    return {p.strip() for p in (header or '').split(';')}


def _test_csp_default_src(app, expect):
    """Assert that the Content-Security-Policy header is the expect param."""
    ext = InvenioApp(app)

    @app.route('/captain_america')
    def captain_america():
        return 'captain america'

    with app.test_client() as client:
        res = client.get('/captain_america')
        assert res.status_code == 200
        assert _normalize_csp_header(
            res.headers.get('Content-Security-Policy')
        ) == _normalize_csp_header(expect)
        assert _normalize_csp_header(
            res.headers.get('X-Content-Security-Policy')
        ) == _normalize_csp_header(expect)


def test_csp_default_src_when_debug_false(app):
    """Test the Content-Security-Policy header when app debug is False."""
    expect = "default-src 'self'; object-src 'none'"
    _test_csp_default_src(app, expect)


def test_csp_default_src_when_debug_true(app):
    """Test the Content-Security-Policy header when app debug is True."""
    app.config['DEBUG'] = True
    expect = "default-src 'self' 'unsafe-inline'; object-src 'none'"
    _test_csp_default_src(app, expect)


def test_empty_csp_when_set_empty(app):
    """Test empty Content-Security-Policy header when set emtpy."""
    app.config['DEBUG'] = True
    app.config['APP_DEFAULT_SECURE_HEADERS']['content_security_policy'] = {}
    expect = None
    _test_csp_default_src(app, expect)


def test_default_health_blueprint(app):
    app.config['APP_HEALTH_BLUEPRINT_ENABLED'] = True
    # Initialize the app
    InvenioApp(app)
    with app.test_client() as client:
        res = client.get('/ping')
        assert res.status_code == 200
