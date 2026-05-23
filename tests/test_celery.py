# SPDX-FileCopyrightText: 2017-2018 CERN.
# SPDX-License-Identifier: MIT

"""Celery test."""


def test_celery():
    """Test celery application."""
    from invenio_app.celery import celery

    celery.loader.import_default_modules()
