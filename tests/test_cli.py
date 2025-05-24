# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
# Copyright (C) 2025 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""CLI test."""

import importlib.metadata

from click.testing import CliRunner


def test_basic_cli():
    """Test version import."""
    from invenio_app.cli import cli

    res = CliRunner().invoke(cli)

    if importlib.metadata.version("click") < "8.2.0":
        # click >= 8.2.0 dropped python3.9 support
        assert res.exit_code == 0
    else:
        assert res.exit_code == 2
