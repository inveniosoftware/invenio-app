# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Flask application factories for Invenio flavours."""

import os
import sys

import pkg_resources
from invenio_base.app import create_app_factory
from invenio_base.wsgi import create_wsgi_factory, wsgi_proxyfix
from invenio_cache import BytecodeCache
from invenio_config import create_config_loader

from .helpers import TrustedHostsMixin

env_prefix = "INVENIO"

invenio_config_loader = create_config_loader(config=None, env_prefix=env_prefix)


def instance_path():
    """Instance path for Invenio.

    Defaults to ``<env_prefix>_INSTANCE_PATH``
     or if environment variable is not set ``<sys.prefix>/var/instance``.
    """
    return os.getenv(env_prefix + "_INSTANCE_PATH") or os.path.join(
        sys.prefix, "var", "instance"
    )


def static_folder():
    """Static folder path.

    Defaults to ``<env_prefix>_STATIC_FOLDER``
    or if environment variable is not set ``<sys.prefix>/var/instance/static``.
    """
    return os.getenv(env_prefix + "_STATIC_FOLDER") or os.path.join(
        instance_path(), "static"
    )


def static_url_path():
    """Static url path.

    Defaults to ``<env_prefix>_STATIC_URL_PATH``
    or if environment variable is not set ``/static``.
    """
    return os.getenv(env_prefix + "_STATIC_URL_PATH") or "/static"


def config_loader(app, **kwargs_config):
    """Configuration loader."""
    invenio_config_loader(app, **kwargs_config)

    # TODO: Move this to invenio_cache.ext.InvenioCache.init_app
    app.jinja_env.cache_size = 1000
    app.jinja_env.bytecode_cache = BytecodeCache(app)


def app_class():
    """Create Flask application class.

    Invenio-Files-REST needs to patch the Werkzeug form parsing in order to
    support streaming large file uploads. This is done by subclassing the Flask
    application class.
    """
    try:
        pkg_resources.get_distribution("invenio-files-rest")
        from invenio_files_rest.app import Flask as FlaskBase
    except pkg_resources.DistributionNotFound:
        from flask import Flask as FlaskBase

    # Add Host header validation via APP_ALLOWED_HOSTS configuration variable.
    class Request(TrustedHostsMixin, FlaskBase.request_class):
        pass

    class Flask(FlaskBase):
        request_class = Request

    return Flask


create_api = create_app_factory(
    "invenio",
    config_loader=config_loader,
    blueprint_entry_points=["invenio_base.api_blueprints"],
    extension_entry_points=["invenio_base.api_apps"],
    converter_entry_points=["invenio_base.api_converters"],
    finalize_app_entry_points=["invenio_base.api_finalize_app"],
    wsgi_factory=wsgi_proxyfix(),
    instance_path=instance_path,
    root_path=instance_path,
    app_class=app_class(),
)
"""Flask application factory for Invenio REST API."""

create_ui = create_app_factory(
    "invenio",
    config_loader=config_loader,
    blueprint_entry_points=["invenio_base.blueprints"],
    extension_entry_points=["invenio_base.apps"],
    converter_entry_points=["invenio_base.converters"],
    finalize_app_entry_points=["invenio_base.finalize_app"],
    wsgi_factory=wsgi_proxyfix(),
    instance_path=instance_path,
    static_folder=static_folder,
    root_path=instance_path,
    static_url_path=static_url_path(),
    app_class=app_class(),
)
"""Flask application factory for Invenio UI."""

create_app = create_app_factory(
    "invenio",
    config_loader=config_loader,
    blueprint_entry_points=["invenio_base.blueprints"],
    extension_entry_points=["invenio_base.apps"],
    converter_entry_points=["invenio_base.converters"],
    finalize_app_entry_points=["invenio_base.finalize_app"],
    wsgi_factory=wsgi_proxyfix(create_wsgi_factory({"/api": create_api})),
    instance_path=instance_path,
    static_folder=static_folder,
    root_path=instance_path,
    static_url_path=static_url_path(),
    app_class=app_class(),
)
"""Flask application factory for combined UI + REST API.

REST API is mounted under ``/api``.
"""
