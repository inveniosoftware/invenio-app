# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2026 CERN.
# Copyright (C) 2022 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests.

The tests in this module use ``app_with_no_limiter`` fixture.
They need to be in a separate module from tests that use ``app`` fixture,
because it modifies the config on a global ``base_app`` and create a Limiter
instance that would influence these tests.
"""

from invenio_app import InvenioApp


def test_headers(app_with_no_limiter):
    """Test headers."""
    app_with_no_limiter.config["RATELIMIT_APPLICATION"] = "1/day"
    ext = InvenioApp(app_with_no_limiter)

    for handler in app_with_no_limiter.logger.handlers:
        ext.limiter.logger.addHandler(handler)

    @app_with_no_limiter.route("/jessica_jones")
    def jessica_jones():
        return "jessica jones"

    @app_with_no_limiter.route("/avengers")
    def avengers():
        return "infinity war"

    with app_with_no_limiter.test_client() as client:
        res = client.get("/jessica_jones")
        assert res.status_code == 200
        assert res.headers["X-RateLimit-Limit"] == "1"
        assert res.headers["X-RateLimit-Remaining"] == "0"
        assert res.headers["X-RateLimit-Reset"]

        res = client.get("/jessica_jones")
        assert res.status_code == 429
        assert res.headers["X-RateLimit-Limit"]
        assert res.headers["X-RateLimit-Remaining"]
        assert res.headers["X-RateLimit-Reset"]

        res = client.get("/avengers")
        assert res.status_code == 429
        assert res.headers["X-Content-Type-Options"]
        assert res.headers["X-Frame-Options"]
        assert res.headers["X-XSS-Protection"]
        assert res.headers["X-RateLimit-Limit"]
        assert res.headers["X-RateLimit-Remaining"]
        assert res.headers["X-RateLimit-Reset"]
