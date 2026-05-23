# SPDX-FileCopyrightText: 2017-2018 CERN.
# SPDX-License-Identifier: MIT

"""CLI application for Invenio flavours."""

from invenio_base.app import create_cli

from .factory import create_app

#: Invenio CLI application.
cli = create_cli(create_app=create_app)
