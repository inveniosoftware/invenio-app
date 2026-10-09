# SPDX-FileCopyrightText: 2017-2018 CERN.
# SPDX-FileCopyrightText: 2025 Graz University of Technology.
# SPDX-License-Identifier: MIT

"""Celery test."""

import os
import pickle
import sys

import pytest
from billiard.reduction import ForkingPickler
from celery.beat import PersistentScheduler, Service


def test_celery():
    """Test celery application."""
    os.environ["INVENIO_SECRET_KEY"] = "CHANGE_ME"
    from invenio_app.celery import celery

    celery.loader.import_default_modules()


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS spawn workaround")
@pytest.mark.parametrize(
    "scheduler_cls", [PersistentScheduler, "celery.beat:PersistentScheduler"]
)
def test_embedded_beat_service_pickle(monkeypatch, tmp_path, scheduler_cls):
    """Embedded Beat must retain its app and scheduler settings under spawn."""
    monkeypatch.setenv("INVENIO_SECRET_KEY", "CHANGE_ME")
    from invenio_app.celery import celery

    app = celery._get_current_object()
    schedule_filename = str(tmp_path / "celerybeat-schedule")
    service = Service(
        app,
        max_interval=17,
        schedule_filename=schedule_filename,
        scheduler_cls=scheduler_cls,
    )

    restored = pickle.loads(ForkingPickler.dumps(service))

    assert restored.app is app
    assert restored.max_interval == 17
    assert restored.schedule_filename == schedule_filename
    assert restored.scheduler_cls == scheduler_cls
    scheduler = restored.get_scheduler(lazy=True)
    assert isinstance(scheduler, PersistentScheduler)
    assert scheduler.app is app
