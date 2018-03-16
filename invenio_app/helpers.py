# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Helpers."""

from __future__ import absolute_import, print_function

from flask import current_app


class TrustedHostsMixin(object):
    """Mixin for reading trusted hosts from application config."""

    @property
    def trusted_hosts(self):
        """Get list of trusted hosts."""
        if current_app:
            return current_app.config.get('APP_ALLOWED_HOSTS', None)
