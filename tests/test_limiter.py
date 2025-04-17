# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

from collections import namedtuple
from unittest.mock import patch

from flask import current_app


def exhaust_and_test_rate_limit_per_second(client, rate_to_exhaust):
    """Helper function to test,per second,rate limits."""
    available_rate = int(rate_to_exhaust.split("per")[0])
    for x in range(0, available_rate):
        assert 200 == client.get("/limited_rate").status_code
    assert 429 == client.get("/limited_rate").status_code


def test_limiter(app):
    """Test the Flask limiter function."""
    with app.test_client() as client:
        exhaust_and_test_rate_limit_per_second(
            client, current_app.config["RATELIMIT_GUEST_USER"]
        )
        for x in range(0, 2):
            assert 200 == client.get("/unlimited_rate").status_code
        assert 200 == client.get("/unlimited_rate").status_code


FakeUser = namedtuple("User", ["is_authenticated"])


@patch("invenio_app.limiter.current_user", FakeUser(is_authenticated=True))
def test_limiter_for_authenticated_user(app):
    """Test the Flask limiter function."""
    with app.test_client() as client:
        exhaust_and_test_rate_limit_per_second(
            client, current_app.config["RATELIMIT_AUTHENTICATED_USER"]
        )
        assert 200 == client.get("/unlimited_rate").status_code


@patch("invenio_app.limiter.current_user", FakeUser(is_authenticated=True))
def test_limiter_for_privileged_user(app, push_rate_limit_to_context):
    """Test the Flask limiter function."""
    with app.test_client() as client:
        exhaust_and_test_rate_limit_per_second(client, push_rate_limit_to_context)

        assert 200 == client.get("/unlimited_rate").status_code
