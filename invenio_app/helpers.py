# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Helpers."""

import os

from flask import current_app, request
from jinja2 import BaseLoader, TemplateNotFound
from uritools import uricompose, urisplit
from werkzeug.utils import cached_property, import_string


class TrustedHostsMixin(object):
    """Mixin for reading trusted hosts from application config."""

    @property
    def trusted_hosts(self):
        """Get list of trusted hosts."""
        if current_app:
            return current_app.config.get("APP_ALLOWED_HOSTS", None)


def get_safe_redirect_target(arg="next", _target=None):
    """Get URL to redirect to and ensure that it is local.

    :param arg: URL argument.
    :returns: The redirect target or ``None``.
    """
    for target in _target, request.args.get(arg), request.referrer:
        redirect = safe_redirect(target)
        if redirect:
            return redirect
    return None


def safe_redirect(target):
    """Ensure redirect is a local redirect."""
    if target:
        redirect_uri = urisplit(target)
        allowed_hosts = current_app.config.get("APP_ALLOWED_HOSTS", [])
        if redirect_uri.host in allowed_hosts:
            return target
        elif redirect_uri.path:
            return uricompose(
                path=redirect_uri.path,
                query=redirect_uri.query,
                fragment=redirect_uri.fragment,
            )
    return None


class ThemeJinjaLoader(BaseLoader):
    """Prefix template loader.

    This loader acts as a wrapper for any type of Jinja loader. Before doing a
    template lookup, the loader sequentially applies prefixes to the template
    name, until a template source is found.

    The prefixes are defined via the ``APP_THEME`` configuration variable.
    """

    def __init__(self, app, loader):
        """Initialize loader.

        :param app: Flask application.
        :param loader: Jinja loader to be wrapped.
        """
        self.app = app
        self.loader = loader

    @cached_property
    def prefixes(self):
        """Return the active prefixes to be used for template lookup."""
        theme = self.app.config.get("APP_THEME", [])
        if isinstance(theme, str):
            theme = [theme]
        return theme

    def _prefixed_templates(self, name):
        template_names = [os.path.join(p, name) for p in self.prefixes]
        return template_names + [name]

    def get_source(self, environment, template):
        """Get the template source, filename and reload helper."""
        for tpl in self._prefixed_templates(template):
            try:
                return self.loader.get_source(environment, tpl)
            except TemplateNotFound:
                pass
        raise TemplateNotFound(template)

    def load(self, environment, name, globals=None):
        """Loads a template."""
        for tpl in self._prefixed_templates(name):
            try:
                return self.loader.load(environment, tpl, globals)
            except TemplateNotFound:
                pass
        raise TemplateNotFound(name)

    def list_templates(self):
        """List all availbale templates."""
        return self.loader.list_templates()


def obj_or_import_string(value, default=None):
    """Import string or return object.

    :params value: Import path or class object to instantiate.
    :params default: Default object to return if the import fails.
    :returns: The imported object.
    """
    if isinstance(value, str):
        return import_string(value)
    elif value:
        return value
    return default
