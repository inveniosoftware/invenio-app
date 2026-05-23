# SPDX-FileCopyrightText: 2017-2018 CERN.
# SPDX-License-Identifier: MIT

"""UI-only WSGI application for Invenio flavours."""

from .factory import create_ui

#: WSGI application for Invenio UI.
application = create_ui()
