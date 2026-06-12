# SPDX-FileCopyrightText: 2017-2026 CERN.
# SPDX-FileCopyrightText: 2025 Graz University of Technology.
# SPDX-License-Identifier: MIT

"""CLI application for Invenio flavours."""

import os
import signal
import socket
import sys
from pathlib import Path

from click import ClickException, echo, group, option, pass_context, secho
from flask import current_app
from flask.cli import ScriptInfo, with_appcontext
from invenio_base.app import create_cli

from .factory import create_app
from .rpc import RPCServer, ServerStop, send_request

#: Invenio CLI application.
cli = create_cli(create_app=create_app)


def _socket_path(value):
    """Resolve the socket path, defaulting to the app instance directory."""
    return Path(value) if value else Path(current_app.instance_path) / "rpc.sock"


def _ensure_socket_is_free(socket_path):
    """Remove a stale socket file, or fail if a server is listening on it."""
    if not socket_path.exists():
        return
    probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        probe.settimeout(1)
        probe.connect(str(socket_path))
    except OSError:
        # nothing is listening, the file was left behind by a dead server
        socket_path.unlink()
    else:
        raise ClickException(f"An RPC server is already listening on {socket_path}.")
    finally:
        probe.close()


def _request_or_fail(socket_path, payload):
    """Send a request, turning connection problems into a CLI error."""
    try:
        return send_request(socket_path, payload)
    except OSError as e:
        raise ClickException(f"No RPC server reachable on {socket_path} ({e}).")


socket_option = option(
    "--socket",
    "socket_path",
    default=None,
    help="Path to the server socket (default: <instance_path>/rpc.sock).",
)


@group()
def rpc_server():
    """RPC server."""


@rpc_server.command("start")
@socket_option
@with_appcontext
def rpc_server_start(socket_path):
    """Start the RPC server."""
    socket_path = _socket_path(socket_path)
    pid_path = socket_path.with_suffix(".pid")
    _ensure_socket_is_free(socket_path)

    # the app is already created thanks to with_appcontext; reuse it for
    # every request instead of creating one per command
    app = current_app._get_current_object()
    server = RPCServer(socket_path, cli, ScriptInfo(create_app=lambda: app))
    os.chmod(socket_path, 0o600)
    pid_path.write_text(str(os.getpid()))

    def stop(signo, frame):
        """Translate SIGTERM into a ServerStop exception."""
        raise ServerStop()

    signal.signal(signal.SIGTERM, stop)
    # stream promptly when output is forwarded to a client terminal
    sys.stdout.reconfigure(line_buffering=True)

    secho(f"RPC server listening on {socket_path} (Press Ctrl+C to stop)", fg="green")
    try:
        server.serve_forever()
    except (KeyboardInterrupt, ServerStop):
        pass
    finally:
        server.server_close()
        socket_path.unlink(missing_ok=True)
        pid_path.unlink(missing_ok=True)


@rpc_server.command(
    "send",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
@socket_option
@with_appcontext
@pass_context
def rpc_server_send(ctx, socket_path):
    """Run a CLI command on the RPC server and relay its output."""
    response = _request_or_fail(_socket_path(socket_path), {"argv": ctx.args})
    if response["stdout"]:
        echo(response["stdout"], nl=False)
    if response["stderr"]:
        echo(response["stderr"], nl=False, err=True)
    sys.exit(response["exit_code"])


@rpc_server.command("ping")
@socket_option
@with_appcontext
def rpc_server_ping(socket_path):
    """Check whether the RPC server responds."""
    response = _request_or_fail(_socket_path(socket_path), {"ping": True})
    if not response.get("pong"):
        raise ClickException("Unexpected response from the RPC server.")
    secho("pong", fg="green")
