# SPDX-FileCopyrightText: 2017-2018 CERN.
# SPDX-License-Identifier: MIT

"""Module tests."""

from werkzeug.test import EnvironBuilder


def wsgi_output(application):
    data = {}

    def start_response(status, headers):
        data["status"] = status
        data["headers"] = headers

    data["output"] = application(
        EnvironBuilder(path="/", method="GET").get_environ(), start_response
    )
    return data


def test_wsgi(wsgi_apps):
    """Test wsgi."""
    create_app, create_ui, create_api = wsgi_apps

    res = wsgi_output(create_app())
    assert res["status"] == "404 NOT FOUND"

    res = wsgi_output(create_ui())
    assert res["status"] == "404 NOT FOUND"

    res = wsgi_output(create_api())
    assert res["status"] == "404 NOT FOUND"
