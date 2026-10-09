# SPDX-FileCopyrightText: 2017-2018 CERN.
# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o.
# SPDX-License-Identifier: MIT

"""Celery application for Invenio flavours."""

import os
import sys

from billiard.reduction import ForkingPickler
from celery import Celery
from flask_celeryext import create_celery_app

from .factory import create_ui

celery = create_celery_app(
    create_ui(
        SENTRY_TRANSPORT="raven.transport.http.HTTPTransport",
        RATELIMIT_ENABLED=False,
    )
)
"""Celery application for Invenio.

Overrides SENTRY_TRANSPORT wih synchronous HTTP transport since Celery does not
deal nicely with the default threaded transport.
"""

# Trigger an app log message upon import. This makes Sentry logging
# work with `get_task_logger(__name__)`.
celery.flask_app.logger.info("Created Celery app")


if sys.platform == "darwin":

    # On macOS billiard starts the prefork pool processes with "spawn", which
    # pickles the Celery app into each of them. Pickling it by value fails on
    # unpicklable config values (lambdas, LocalProxies, ...). Pickle it by
    # reference instead, so that each pool process imports this module and
    # creates its own fully set up app.

    def _load_celery_app():
        """Return the real Celery app object behind the ``celery`` proxy.

        Called when a spawned pool process unpickles the app. Unpickling
        resolves this function by reference, which imports this module and
        so configures the process's current Celery app. ``celery`` is a
        ``celery.local.Proxy`` and ``_get_current_object()`` returns the
        current app it points to (``celery._state.get_current_app()``).
        """
        return celery._get_current_object()

    def _reduce_celery_app(app):
        """Pickle the Celery app as a reference to this module.

        Returns a ``(callable, args)`` tuple in the ``__reduce__`` protocol.
        Pickle stores the callable by reference (module and qualified name,
        here ``invenio_app.celery._load_celery_app``), not by value. On
        unpickling it imports the module, looks up the callable and calls
        it with ``args`` (none here) to get the app.
        """
        return _load_celery_app, ()

    ForkingPickler.register(Celery, _reduce_celery_app)

    # Make celery's prefork process initializer set up the fast_trace_task
    # optimization in the spawned processes, which inherit this variable.
    os.environ.setdefault("FORKED_BY_MULTIPROCESSING", "1")
