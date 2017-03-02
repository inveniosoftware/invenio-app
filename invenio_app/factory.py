# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Flask application factories for Invenio flavours."""

from __future__ import absolute_import, print_function

import os
import sys

import pkg_resources
from invenio_base.app import create_app_factory
from invenio_base.wsgi import create_wsgi_factory, wsgi_proxyfix
from invenio_config import create_config_loader
from jinja2 import ChoiceLoader, FileSystemLoader

env_prefix = 'INVENIO'

invenio_config_loader = create_config_loader(
    config=None, env_prefix=env_prefix
)

instance_path = os.getenv(env_prefix + '_INSTANCE_PATH') or \
    os.path.join(sys.prefix, 'var', 'instance')
"""Instance path for Invenio.

Defaults to ``<env_prefix>_INSTANCE_PATH`` or if environment variable is not
set ``<sys.prefix>/var/instance``.
"""

static_folder = os.getenv(env_prefix + '_STATIC_FOLDER') or \
    os.path.join(instance_path, 'static')
"""Static folder path.

Defaults to ``<env_prefix>_STATIC_FOLDER`` or if environment variable is not
set ``<sys.prefix>/var/instance/static``.
"""


def config_loader(app, **kwargs_config):
    """Configuration loader.

    Adds support for loading templates from the Flask application's instance
    folder (``<instance_folder>/templates``).
    """
    # This is the only place customize the Flask application right after
    # it has been created, but before all extensions etc are loaded.
    local_templates_path = os.path.join(app.instance_path, 'templates')
    if os.path.exists(local_templates_path):
        # Let's customize the template loader to look into packages
        # and application templates folders.
        app.jinja_loader = ChoiceLoader([
            FileSystemLoader(local_templates_path),
            app.jinja_loader,
        ])

    # FIXME: Add Jinja byte code caching.
    # app.jinja_options = dict(
    #     app.jinja_options,
    #     cache_size=1000,
    #     bytecode_cache=RedisBytecodeCache(app)
    # )

    invenio_config_loader(app, **kwargs_config)


def app_class():
    """Determine Flask application class.

    Invenio-Files-REST needs to patch the Werkzeug form parsing in order to
    support streaming large file uploads. This is done by subclassing the Flask
    application class.
    """
    try:
        pkg_resources.get_distribution('invenio-files-rest')
        from invenio_files_rest.app import Flask
        return Flask
    except pkg_resources.DistributionNotFound:
        from flask import Flask
        return Flask


create_api = create_app_factory(
    'invenio',
    config_loader=config_loader,
    blueprint_entry_points=['invenio_base.api_blueprints'],
    extension_entry_points=['invenio_base.api_apps'],
    converter_entry_points=['invenio_base.api_converters'],
    wsgi_factory=wsgi_proxyfix(),
    instance_path=instance_path,
    app_class=app_class(),
)
"""Flask application factory for Invenio REST API."""

create_ui = create_app_factory(
    'invenio',
    config_loader=config_loader,
    blueprint_entry_points=['invenio_base.blueprints'],
    extension_entry_points=['invenio_base.apps'],
    converter_entry_points=['invenio_base.converters'],
    wsgi_factory=wsgi_proxyfix(),
    instance_path=instance_path,
    static_folder=static_folder,
)
"""Flask application factory for Invenio UI."""

create_app = create_app_factory(
    'invenio',
    config_loader=config_loader,
    blueprint_entry_points=['invenio_base.blueprints'],
    extension_entry_points=['invenio_base.apps'],
    converter_entry_points=['invenio_base.converters'],
    wsgi_factory=wsgi_proxyfix(create_wsgi_factory({'/api': create_api})),
    instance_path=instance_path,
    static_folder=static_folder,
)
"""Flask application factory for combined UI + REST API.

REST API is mounted under ``/api``.
"""
