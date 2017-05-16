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

"""Module tests."""

from __future__ import absolute_import, print_function

from flask import Flask

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

    @app.route('/avangers')
    def avangers():
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

        res = client.get('/avangers')
        assert res.status_code == 200
        assert res.headers['X-Content-Security-Policy']
        assert res.headers['X-Content-Type-Options']
        assert res.headers['X-Frame-Options']
        assert res.headers['X-XSS-Protection']
        assert res.headers['X-RateLimit-Limit']
        assert res.headers['X-RateLimit-Remaining']
        assert res.headers['X-RateLimit-Reset']
