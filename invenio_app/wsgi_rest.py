# SPDX-FileCopyrightText: 2017-2018 CERN.
# SPDX-License-Identifier: MIT

"""REST-only WSGI application for Invenio flavours."""

from .factory import create_api

#: WSGI application for Invenio REST API.
application = create_api()
