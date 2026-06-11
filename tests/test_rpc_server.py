# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2026 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""RPC server tests."""

import json
import socket
import tempfile
import threading
from pathlib import Path

import pytest

from invenio_app.cli import RPCServer, send_request


@pytest.fixture()
def rpc_socket():
    """A running RPC server on a temporary socket.

    Uses a short-lived directory under /tmp because AF_UNIX paths are
    limited to ~104 bytes on macOS, which pytest's tmp_path exceeds.
    """
    tmp_dir = tempfile.TemporaryDirectory(prefix="rpc", dir="/tmp")
    socket_path = Path(tmp_dir.name) / "rpc.sock"
    server = RPCServer(socket_path)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield socket_path
    server.shutdown()
    server.server_close()
    tmp_dir.cleanup()


def test_ping(rpc_socket):
    """The server answers a ping."""
    assert send_request(rpc_socket, {"ping": True}) == {"pong": True}


def test_request_larger_than_a_socket_buffer(rpc_socket):
    """Requests are framed by line, not by a fixed read size."""
    request = {"ping": True, "padding": "x" * 100_000}
    assert send_request(rpc_socket, request) == {"pong": True}


def test_invalid_json(rpc_socket):
    """A malformed request gets an error response, not a hangup."""
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.connect(str(rpc_socket))
        s.sendall(b"not json\n")
        with s.makefile("rb") as f:
            response = json.loads(f.readline())
    assert response["exit_code"] == 2
    assert "not valid JSON" in response["stderr"]


def test_argv_must_be_a_list_of_strings(rpc_socket):
    """A non-argv payload is rejected."""
    response = send_request(rpc_socket, {"argv": "collect"})
    assert response["exit_code"] == 2
    assert "list of strings" in response["stderr"]
