# SPDX-FileCopyrightText: 2017-2026 CERN.
# SPDX-FileCopyrightText: 2025 Graz University of Technology.
# SPDX-License-Identifier: MIT

"""CLI application for Invenio flavours."""

import array
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


class ServerStop(BaseException):
    """Raised by the SIGTERM handler to stop the server.

    Derives from BaseException so a terminating signal that lands during a
    command is not mistaken for the command's own SystemExit and reported
    as its exit code.
    """


def error_response(message):
    """Build the response for a malformed request."""
    return {"exit_code": 2, "stdout": "", "stderr": message + "\n"}


def recv_request(sock):
    """Read one JSON line plus any file descriptors sent with it.

    Also reports whether ancillary data was truncated (i.e. more
    descriptors arrived than fit the buffer), so the caller can reject
    the request instead of running it with silently dropped descriptors.
    """
    buf = b""
    fds = []
    truncated = False
    fd_size = array.array("i").itemsize
    while b"\n" not in buf:
        data, ancdata, flags, _ = sock.recvmsg(65536, socket.CMSG_SPACE(2 * fd_size))
        if not data:
            break
        truncated = truncated or bool(flags & socket.MSG_CTRUNC)
        for level, ctype, cdata in ancdata:
            if level == socket.SOL_SOCKET and ctype == socket.SCM_RIGHTS:
                received = array.array("i")
                received.frombytes(cdata[: len(cdata) - (len(cdata) % fd_size)])
                fds.extend(received)
        buf += data
    return buf, fds, truncated


class RPCRequestHandler(socketserver.BaseRequestHandler):
    """Handler for newline-delimited JSON requests."""

    def handle(self):
        """Answer a single request with a single JSON line."""
        line, fds, truncated = recv_request(self.request)
        try:
            if not line:
                return

            if truncated:
                self.respond(
                    error_response("Truncated file descriptor data (too many fds).")
                )
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

            if fds:
                if len(fds) != 2:
                    self.respond(
                        error_response(
                            "Expected two file descriptors (stdout, stderr)."
                        )
                    )
                    return
                self.respond(self.server.execute_redirected(argv, *fds))
            else:
                self.respond(self.server.execute(argv))
        finally:
            for fd in fds:
                try:
                    os.close(fd)
                except OSError:
                    pass

    def respond(self, payload):
        """Write a response as a single JSON line."""
        self.request.sendall(json.dumps(payload).encode("utf-8") + b"\n")


class RPCServer(socketserver.UnixStreamServer):
    """Serve invenio CLI commands on a Unix domain socket.

    Requests are handled one at a time, which also serializes commands sent
    by concurrent clients.
    """

    def __init__(self, socket_path, script_info):
        """Construct."""
        self.script_info = script_info
        super().__init__(str(socket_path), RPCRequestHandler)

    def run_cli(self, argv):
        """Run a CLI command and return its exit code.

        Output goes to whatever ``sys.stdout``/``sys.stderr`` point at when
        called. The shared ``ScriptInfo`` caches the Flask app, so only the
        first command pays for the app creation. Each command runs in a
        fresh app context (commands skip pushing their own when one is
        already active), so ``flask.g`` and teardown handlers — e.g. the
        SQLAlchemy session removal — behave per command, not per server
        lifetime. ``standalone_mode`` makes click print usage errors itself
        and exit with its usual exit codes.
        """
        try:
            with self.script_info.load_app().app_context():
                cli.main(
                    args=argv,
                    prog_name="invenio",
                    obj=self.script_info,
                    standalone_mode=True,
                )
        except SystemExit as e:
            if e.code is None:
                return 0
            if isinstance(e.code, int):
                return e.code
            print(e.code, file=sys.stderr)
            return 1
        except Exception:
            traceback.print_exc()
            return 1
        return 0

    def execute(self, argv):
        """Run a CLI command, capturing Python-level output in the response.

        Output written directly to the file descriptors by subprocesses
        (e.g. webpack builds) goes to the server's own stdout/stderr.
        """
        stdout, stderr = StringIO(), StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = self.run_cli(argv)
        return {
            "exit_code": exit_code,
            "stdout": stdout.getvalue(),
            "stderr": stderr.getvalue(),
        }

    def execute_redirected(self, argv, stdout_fd, stderr_fd):
        """Run a CLI command with output sent straight to the given fds.

        The client passes its own stdout/stderr (or a log file) over the
        socket and the command's output streams there live. Both levels
        are redirected: the process-level descriptors 1/2 (so subprocess
        output like webpack builds arrives too) and the Python-level
        ``sys.stdout``/``sys.stderr`` (for click/print output).
        """
        sys.stdout.flush()
        sys.stderr.flush()
        saved_stdout, saved_stderr = os.dup(1), os.dup(2)
        os.dup2(stdout_fd, 1)
        os.dup2(stderr_fd, 2)
        # fdopen takes ownership, so hand it duplicates; the handler closes
        # the received descriptors itself
        out = os.fdopen(os.dup(stdout_fd), "w", buffering=1)
        err = os.fdopen(os.dup(stderr_fd), "w", buffering=1)
        try:
            with redirect_stdout(out), redirect_stderr(err):
                exit_code = self.run_cli(argv)
        finally:
            # restore our own stdio before anything that can raise — a
            # close() flushes and fails on a client-closed pipe, and that
            # must not leave fd 1/2 pointing at the dead client
            os.dup2(saved_stdout, 1)
            os.dup2(saved_stderr, 2)
            os.close(saved_stdout)
            os.close(saved_stderr)
            for stream in (out, err):
                try:
                    stream.close()
                except OSError:
                    pass
        return {"exit_code": exit_code}


def send_request(socket_path, payload, fds=None):
    """Send one request to a server and return the decoded response.

    With ``fds`` (stdout, stderr) the command output is streamed straight
    to those descriptors and the response carries only the exit code.
    """
    line = json.dumps(payload).encode("utf-8") + b"\n"
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.connect(str(socket_path))
        if fds:
            s.sendmsg(
                [line], [(socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array("i", fds))]
            )
        else:
            s.sendall(line)
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
