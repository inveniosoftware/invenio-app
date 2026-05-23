# SPDX-FileCopyrightText: 2017-2018 CERN.
# SPDX-License-Identifier: MIT

"""Helper tests."""

from urllib.parse import quote_plus

import pytest

from invenio_app.helpers import get_safe_redirect_target


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (
            "https://example.org/search?page=1&q=&keywords=taxonomy&keywords=animali",
            "/search?page=1&q=&keywords=taxonomy&keywords=animali",
        ),
        ("/search?page=1&size=20", "/search?page=1&size=20"),
        ("https://localhost/search?page=1", "https://localhost/search?page=1"),
    ],
)
def test_get_safe_redirect_target(app, test_input, expected):
    """Test that only "localhost" is a trusted absolute redirect target."""
    with app.test_request_context("/?next={0}".format(quote_plus(test_input))):
        assert get_safe_redirect_target() == expected
