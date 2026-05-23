# SPDX-FileCopyrightText: 2017-2018 CERN.
# SPDX-FileCopyrightText: 2025 Graz University of Technology.
# SPDX-License-Identifier: MIT

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
