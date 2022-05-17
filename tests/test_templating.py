# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test Jinja template loading."""

import shutil
import tempfile
from os import environ
from os.path import dirname, join

import pytest
from flask import Blueprint, render_template
from jinja2 import TemplateNotFound

from invenio_app.factory import create_ui


#
# Fixtures
#
@pytest.fixture()
def instance_path():
    """Fixture for creating an instance path."""
    path = tempfile.mkdtemp()
    environ.update(
        INVENIO_INSTANCE_PATH=environ.get("INSTANCE_PATH", path),
    )
    yield path
    environ.pop("INVENIO_INSTANCE_PATH", None)
    shutil.rmtree(path)


@pytest.fixture()
def blueprint():
    """Blueprint for loading templates."""
    # This blueprint picks up the tests/templates/ folder, so that we can
    # render templates from inside this folder.
    return Blueprint("tests", __name__, template_folder="templates")


@pytest.fixture()
def notheme_app(instance_path, blueprint):
    """Application without template theming."""
    app = create_ui()
    app.register_blueprint(blueprint)
    with app.app_context():
        yield app


@pytest.fixture()
def theme_app(instance_path, blueprint):
    """Application with template theming."""
    app = create_ui(APP_THEME=["semantic-ui", "bootstrap3"])
    app.register_blueprint(blueprint)
    with app.app_context():
        yield app


@pytest.fixture()
def theme_app_instance_templates(theme_app):
    """Copy templates into instance folder."""
    # Fixture depends on theme_app to ensure the correct instance path is used.
    src = join(dirname(__file__), "instance/templates")
    dst = join(theme_app.instance_path, "templates")
    shutil.copytree(src, dst)
    yield src
    shutil.rmtree(dst)


#
# Tests
#
def test_notheme(notheme_app):
    """Test template loading order *without* themes."""
    assert render_template("base.html") == "base"
    assert render_template("fallback.html") == "fallback-base"
    assert render_template("only.html") == "only-base"

    # Theme templates can also be accessed via full path (not true for base)
    assert render_template("semantic-ui/base.html") == "semantic-ui"
    assert render_template("bootstrap3/base.html") == "bootstrap3"
    assert render_template("bootstrap3/fallback.html") == "fallback-bootstrap3"

    # Not found template
    assert pytest.raises(TemplateNotFound, render_template, "invalid.html")


def test_theme(theme_app):
    """Test template loading order *with* themes configured."""
    # Primary theme defines base.html
    assert render_template("base.html") == "semantic-ui"
    # Primary theme does not define fallback.html so using fallback
    assert render_template("fallback.html") == "fallback-bootstrap3"
    # Primary and secondary theme does not define only.html so using fallback
    # to normal loading
    assert render_template("only.html") == "only-base"

    # Theme templates can also be accessed via full path (not true for base)
    assert render_template("semantic-ui/base.html") == "semantic-ui"
    assert render_template("bootstrap3/base.html") == "bootstrap3"

    # Not found template
    assert pytest.raises(TemplateNotFound, render_template, "invalid.html")


def test_theme_with_instance_templates(theme_app_instance_templates):
    """Test template loading order *with* themes configured."""
    assert render_template("instance.html") == "instance-only-semantic-ui"
    # Primary theme defines base.html
    assert render_template("base.html") == "instance-semantic-ui"
    # Primary theme does not define fallback.html so using fallback
    assert render_template("fallback.html") == "instance-fallback-bootstrap3"
    # Primary and secondary theme does not define only.html so using fallback
    # to normal loading
    assert render_template("only.html") == "instance-only-base"

    # Theme templates can also be accessed via full path (not true for base)
    assert render_template("semantic-ui/base.html") == "instance-semantic-ui"
    assert render_template("bootstrap3/base.html") == "instance-bootstrap3"

    # Instance does not defined noinstance.html
    assert render_template("noinstance.html") == "noinstance-semantic-ui"

    # Not found template
    assert pytest.raises(TemplateNotFound, render_template, "invalid.html")


def test_list_templaes(theme_app):
    """Test list templates."""
    assert sorted(theme_app.jinja_env.loader.list_templates()) == [
        "base.html",
        "bootstrap3/base.html",
        "bootstrap3/fallback.html",
        "fallback.html",
        "only.html",
        "semantic-ui/base.html",
        "semantic-ui/noinstance.html",
    ]
