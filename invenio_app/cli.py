# SPDX-FileCopyrightText: 2017-2026 CERN.
# SPDX-FileCopyrightText: 2025 Graz University of Technology.
# SPDX-License-Identifier: MIT

"""CLI application for Invenio flavours."""

import json
import os
import signal
import socket
import socketserver
import sys
import traceback
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from click import ClickException, echo, group, option, pass_context, secho
from flask import current_app
from flask.cli import ScriptInfo, with_appcontext
from invenio_base.app import create_cli

from .factory import create_app

#: Invenio CLI application.
cli = create_cli(create_app=create_app)


def error_response(message):
    """Build the response for a malformed request."""
    return {"exit_code": 2, "stdout": "", "stderr": message + "\n"}


class RPCRequestHandler(socketserver.StreamRequestHandler):
    """Handler for newline-delimited JSON requests."""

    def handle(self):
        """Answer a single request with a single JSON line."""
        line = self.rfile.readline()
        if not line:
            return

        try:
            request = json.loads(line)
        except ValueError:
            self.respond(error_response("Request is not valid JSON."))
            return

        if request.get("ping"):
            self.respond({"pong": True})
            return

        argv = request.get("argv")
        if not isinstance(argv, list) or not all(isinstance(a, str) for a in argv):
            self.respond(error_response("'argv' must be a list of strings."))
            return

        self.respond(self.server.execute(argv))

    def respond(self, payload):
        """Write a response as a single JSON line."""
        self.wfile.write(json.dumps(payload).encode("utf-8") + b"\n")


class RPCServer(socketserver.UnixStreamServer):
    """Serve invenio CLI commands on a Unix domain socket.

    Requests are handled one at a time, which also serializes commands sent
    by concurrent clients.
    """

    def __init__(self, socket_path, script_info):
        """Construct."""
        self.script_info = script_info
        super().__init__(str(socket_path), RPCRequestHandler)

    def execute(self, argv):
        """Run a CLI command and capture its output and exit code.

        The shared ``ScriptInfo`` caches the Flask app, so only the first
        command pays for the app creation. Only Python-level output is
        captured; output written directly to the file descriptors by
        subprocesses (e.g. webpack builds) goes to the server's own
        stdout/stderr. ``standalone_mode`` makes click print usage errors
        itself and exit with its usual exit codes.
        """
        stdout, stderr = StringIO(), StringIO()
        exit_code = 0
        with redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                cli.main(
                    args=argv,
                    prog_name="invenio",
                    obj=self.script_info,
                    standalone_mode=True,
                )
            except SystemExit as e:
                if isinstance(e.code, int):
                    exit_code = e.code
                elif e.code is not None:
                    stderr.write(f"{e.code}\n")
                    exit_code = 1
            except Exception:
                traceback.print_exc(file=stderr)
                exit_code = 1
        return {
            "exit_code": exit_code,
            "stdout": stdout.getvalue(),
            "stderr": stderr.getvalue(),
        }


def send_request(socket_path, payload):
    """Send one request to a server and return the decoded response."""
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.connect(str(socket_path))
        s.sendall(json.dumps(payload).encode("utf-8") + b"\n")
        with s.makefile("rb") as f:
            return json.loads(f.readline())


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
    server = RPCServer(socket_path, ScriptInfo(create_app=lambda: app))
    os.chmod(socket_path, 0o600)
    pid_path.write_text(str(os.getpid()))
    signal.signal(signal.SIGTERM, lambda signo, frame: sys.exit(0))

    secho(f"RPC server listening on {socket_path} (Press Ctrl+C to stop)", fg="green")
    try:
        server.serve_forever()
    except (KeyboardInterrupt, SystemExit):
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
