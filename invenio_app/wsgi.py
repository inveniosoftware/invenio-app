# SPDX-FileCopyrightText: 2017-2018 CERN.
# SPDX-License-Identifier: MIT

"""UI + REST WSGI application for Invenio flavours."""

from .factory import create_app

application = create_app()
"""Combined UI + REST Flask application.

REST API is mounted under ``/api``.
"""
