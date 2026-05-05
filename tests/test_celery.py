# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
# Copyright (C) 2025 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Celery test."""

import os


def test_celery():
    """Test celery application."""
    os.environ["INVENIO_SECRET_KEY"] = "CHANGE_ME"
    from invenio_app.celery import celery

    celery.loader.import_default_modules()
