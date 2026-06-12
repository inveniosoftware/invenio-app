# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2026 CERN.
# Copyright (C) 2025 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""RPC server running CLI commands in a long-lived process.

Clients (e.g. invenio-cli) send one JSON line per request over a Unix
domain socket (``{"argv": [...]}``) and get one JSON line back. When the
request carries the client's stdout/stderr file descriptors (SCM_RIGHTS),
the command output streams straight to them and the response is only the
exit code; otherwise the captured output is returned on the response.
"""

import array
import json
import os
import socket
import socketserver
import sys
import traceback
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO


class ServerStop(BaseException):
    """Raised by a SIGTERM handler to stop the server.

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
    """Serve commands of a click CLI on a Unix domain socket.

    Requests are handled one at a time, which also serializes commands sent
    by concurrent clients.
    """

    def __init__(self, socket_path, cli, script_info):
        """Construct."""
        self.cli = cli
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
                self.cli.main(
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
