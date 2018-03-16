# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

from __future__ import absolute_import, print_function

from flask import request

from invenio_app.factory import create_ui


def test_version():
    """Test version import."""
    from invenio_app import __version__
    assert __version__


def test_config_loader():
    """Test config loader."""
    app = create_ui()
    assert 'cache_size' in app.jinja_options


def test_trusted_hosts():
    """Test trusted hosts configuration."""
    app = create_ui(
        APP_ALLOWED_HOSTS=['example.org', 'www.example.org'],
        APP_ENABLE_SECURE_HEADERS=False,
    )

    @app.route('/')
    def index():
        return request.host

    with app.test_client() as client:
        res = client.get('/', headers={'Host': 'attacker.org'})
        assert res.status_code == 400

        res = client.get('/', headers={'Host': 'example.org'})
        assert res.status_code == 200

        res = client.get('/', headers={'Host': 'www.example.org'})
        assert res.status_code == 200

    # Make sure X-Forwarded-Host can be used as well.
    with app.test_client() as client:
        res = client.get('/', headers={
            'Host': 'example.org',
            'X-Forwarded-Host': 'attacker.org'
        })
        assert res.status_code == 400
