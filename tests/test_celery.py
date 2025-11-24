# SPDX-FileCopyrightText: 2017-2018 CERN.
# SPDX-FileCopyrightText: 2025 Graz University of Technology.
# SPDX-License-Identifier: MIT

"""Celery test."""

import os


def test_celery():
    """Test celery application."""
    os.environ["INVENIO_SECRET_KEY"] = "CHANGE_ME"
    from invenio_app.celery import celery

    celery.loader.import_default_modules()
