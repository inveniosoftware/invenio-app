# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2026 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""RPC server tests."""

import json
import os
import socket
import tempfile
import threading
from pathlib import Path

import pytest
from flask import g
from flask.cli import ScriptInfo

from invenio_app.cli import cli
from invenio_app.rpc import RPCServer, send_request


@pytest.fixture()
def rpc_socket(base_app):
    """A running RPC server on a temporary socket.

    Uses a short-lived directory under /tmp because AF_UNIX paths are
    limited to ~104 bytes on macOS, which pytest's tmp_path exceeds.
    """
    tmp_dir = tempfile.TemporaryDirectory(prefix="rpc", dir="/tmp")
    socket_path = Path(tmp_dir.name) / "rpc.sock"
    server = RPCServer(socket_path, cli, ScriptInfo(create_app=lambda: base_app))
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


def test_command_stdout_and_exit_code(rpc_socket):
    """A successful command returns its stdout and exit code 0."""
    response = send_request(rpc_socket, {"argv": ["--help"]})
    assert response["exit_code"] == 0
    assert "Usage: invenio" in response["stdout"]
    assert response["stderr"] == ""


def test_unknown_command(rpc_socket):
    """Usage errors come back on stderr with click's exit code."""
    response = send_request(rpc_socket, {"argv": ["definitely-not-a-command"]})
    assert response["exit_code"] == 2
    assert "No such command" in response["stderr"]


def _read_all(fd):
    """Read from fd until EOF."""
    chunks = []
    while chunk := os.read(fd, 4096):
        chunks.append(chunk)
    os.close(fd)
    return b"".join(chunks)


def test_output_streams_to_passed_fds(rpc_socket):
    """With fds attached, output streams to them and only the code returns."""
    out_read, out_write = os.pipe()
    err_read, err_write = os.pipe()
    response = send_request(
        rpc_socket, {"argv": ["--help"]}, fds=[out_write, err_write]
    )
    # close our copies so reading the pipes terminates once the server
    # closes its received descriptors
    os.close(out_write)
    os.close(err_write)

    assert response == {"exit_code": 0}
    assert b"Usage: invenio" in _read_all(out_read)
    assert _read_all(err_read) == b""


def test_wrong_fd_count_is_rejected(rpc_socket):
    """Sending a single fd is an error, not a crash."""
    read_end, write_end = os.pipe()
    response = send_request(rpc_socket, {"argv": ["--help"]}, fds=[write_end])
    os.close(write_end)
    os.close(read_end)
    assert response["exit_code"] == 2
    assert "two file descriptors" in response["stderr"]


def test_too_many_fds_are_rejected(rpc_socket):
    """Descriptors beyond stdout/stderr truncate and reject the request."""
    pipes = [os.pipe() for _ in range(3)]
    response = send_request(
        rpc_socket, {"argv": ["--help"]}, fds=[write_end for _, write_end in pipes]
    )
    for read_end, write_end in pipes:
        os.close(read_end)
        os.close(write_end)
    assert response["exit_code"] == 2
    assert "Truncated" in response["stderr"]


def test_each_command_gets_a_fresh_app_context(rpc_socket, base_app):
    """flask.g must not leak from one command into the next."""

    @base_app.cli.command("g-probe")
    def g_probe():
        """Print the leftover value, then pollute flask.g."""
        print(g.get("probe"))
        g.probe = "leaked"

    first = send_request(rpc_socket, {"argv": ["g-probe"]})
    second = send_request(rpc_socket, {"argv": ["g-probe"]})
    assert first["stdout"] == "None\n"
    assert second["stdout"] == "None\n"


def test_server_survives_a_client_with_closed_pipes(rpc_socket):
    """A broken client pipe must not wedge the server's own stdio."""
    out_read, out_write = os.pipe()
    err_read, err_write = os.pipe()
    # close the read ends so the server writes into broken pipes
    os.close(out_read)
    os.close(err_read)
    try:
        send_request(rpc_socket, {"argv": ["--help"]}, fds=[out_write, err_write])
    except ValueError:
        pass  # the connection may drop without a response
    os.close(out_write)
    os.close(err_write)

    assert send_request(rpc_socket, {"ping": True}) == {"pong": True}
    assert send_request(rpc_socket, {"argv": ["--help"]})["exit_code"] == 0
