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

"""Invenio App configuration.

Please also see
`Flask-Limiter <https://flask-limiter.readthedocs.io/en/stable/>`_ and
`Flask-Talisman <https://github.com/GoogleCloudPlatform/flask-talisman/>`__ for
many more configuration options.
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

For development you can set ```DEBUG = True``` to disable any side effects
such as force ``https`` redirect on your development environment.

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
        'default-src': '\'self\'',
    },
    'content_security_policy_report_uri': None,
    'content_security_policy_report_only': False,
    'session_cookie_secure': True,
    'session_cookie_http_only': True
}
"""Default Secure Headers.

.. note:: Overwrite
    `Flask-Talisman
    <https://github.com/GoogleCloudPlatform/flask-talisman>`_

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
