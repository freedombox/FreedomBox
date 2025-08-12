# SPDX-License-Identifier: AGPL-3.0-or-later
"""The main method for a daemon that runs privileged methods."""

import io
import json
import logging
import os
import pathlib
import pwd
import socket
import socketserver
import struct
import sys
import time
import traceback

import systemd.daemon

from . import __version__, actions
from . import app as app_module
from . import log, module_loader

logger = logging.getLogger(__name__)

address = pathlib.Path('/run/freedombox/privileged.socket')

FREEDOMBOX_PROCESS_USER = 'plinth'

MAX_REQUEST_LENGTH = 1_000_000

idle_shutdown_time: int | None = 5 * 60  # 5 minutes

freedombox_develop = False


class RequestHandler(socketserver.StreamRequestHandler):
    """Handle a single streaming request.

    It is instantiated once per connection to the server. The overridden
    handle() method implements communication with the newly connected client.
    """

    def _read_request(self) -> str:
        """Return a single request read from the client."""
        request_data = self.rfile.read(MAX_REQUEST_LENGTH + 1)
        if len(request_data) > MAX_REQUEST_LENGTH:
            raise ValueError('Request too large')

        try:
            request = request_data.decode('utf-8')
        except UnicodeError:
            raise ValueError('Invalid Unicode in request')

        return request

    def _write_response(self, response: str | io.BufferedReader):
        """Write a single response to the client."""
        if isinstance(response, str):
            self.wfile.write(response.encode('utf-8'))
        else:
            for chunk in response:
                self.wfile.write(chunk)

    def handle(self) -> None:
        """Handle a new connection from a client."""
        try:
            request = self._read_request()
            response_string = actions.privileged_handle_json_request(request)
        except Exception as exception:
            logger.exception('Error running privileged request: %s', exception)
            response = {
                'result': 'exception',
                'exception': {
                    'module': type(exception).__module__,
                    'name': type(exception).__name__,
                    'args': exception.args,
                    'traceback': traceback.format_tb(exception.__traceback__)
                }
            }
            response_string = json.dumps(response)

        self._write_response(response_string)


class Server(socketserver.ThreadingUnixStreamServer):
    """Server to handle privileged request.

    Requests from any process with UID other than from FreedomBox daemon user
    or root will be denied.

    If the server does not receive a request for idle_shutdown_time seconds and
    no requests are being processed, then serve_forever() will raise
    TimeoutError (so that the program can catch it and exit).

    If the daemon is spawned by systemd socket activation, then systemd
    provided socket is re-used (no bind() and listen() calls are made on it)
    and it will not be closed after the server is shutdown. If a daemon is
    spawned without socket activation, unix socket file is created with
    appropriate permissions after the parent directory is created. socket
    object is created, bind() and listen() calls will be made on the socket.
    When server is shutdown, close() is called on the socket.
    """

    def __init__(self, address, *args, **kwargs):
        """Initialize the server."""
        # Retrieve FreedomBox process UID
        user_info = pwd.getpwnam(FREEDOMBOX_PROCESS_USER)
        self.allowed_peer_uids = [0, user_info.pw_uid]

        # Used to auto-shutdown service
        self.last_request_time = time.time()

        self.listen_fd = self._get_listen_fd()
        if self.listen_fd:
            logger.info('systemd socket activated.')
            self.socket = socket.fromfd(self.listen_fd, socket.AF_UNIX,
                                        socket.SOCK_STREAM)
            self.server_address = self.socket.getsockname()
            super(socketserver.TCPServer,
                  self).__init__(address, *args, **kwargs)
        else:
            logger.info('systemd service activated.')
            address_path = pathlib.Path(address)
            address_path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
            address_path.unlink(missing_ok=True)
            super().__init__(address, *args, **kwargs)
            address_path.chmod(0o666)  # All users are allowed to connect

    def server_bind(self):
        """Called by constructor to activate the server.

        Do nothing if socket-activated by systemd.
        """
        if not self.listen_fd:
            super().server_bind()

    def server_activate(self):
        """Called by constructor to activate the server.

        Do nothing if socket-activated by systemd.
        """
        if not self.listen_fd:
            super().server_activate()

    def server_close(self):
        """Called to clean-up the server.

        Don't close the socket if socket-activated by systemd.
        """
        if not self.listen_fd:
            # Not called with systemd socket activation. We are responsible for
            # cleaning up the socket file we created.
            super().server_close()
            pathlib.Path(str(self.server_address)).unlink(missing_ok=True)
        else:
            # Don't close the socket, systemd is still using it for next
            # invocation.
            pass

    def service_actions(self):
        """Called from serve_forever() loop. Shutdown service if unused."""
        super().service_actions()

        if idle_shutdown_time is None:
            return

        if time.time() - self.last_request_time < idle_shutdown_time:
            return

        if not isinstance(self._threads, list):
            return

        if any(thread.is_alive() for thread in self._threads):
            return

        # Raise an exception in the serve_forever() loop.
        raise TimeoutError()

    def _get_listen_fd(self):
        """Return the listening socket from systemd socket activation."""
        listen_fds = systemd.daemon.listen_fds(unset_environment=True)
        if len(listen_fds) == 0:
            # Activated without socket activation.
            return None

        if len(listen_fds) > 1:
            # Activated with multiple listening sockets. We didn't configure
            # our .socket unit like this. This is unexpected.
            return None

        listen_fd = listen_fds[0]
        if not systemd.daemon.is_socket_unix(listen_fd, socket.SOCK_STREAM,
                                             listening=1):
            # Socket is not a AF_UNIX socket, it is not SOCK_STREAM socket, or
            # listen() has not been called on it. This is unexpected.
            return None

        return listen_fd

    def verify_request(self, request, client_address) -> bool:
        """Return False if the request must be denied."""
        creds = request.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED,
                                   struct.calcsize('3i'))
        _, uid, _ = struct.unpack('3i', creds)
        if uid not in self.allowed_peer_uids:
            return False

        self.last_request_time = time.time()

        return True


def main() -> None:
    """Start the server, listen on socket, and serve forever."""
    global freedombox_develop, idle_shutdown_time

    log.action_init()

    logger.info('FreedomBox privileged daemon: %s', __version__)

    if os.getenv('FREEDOMBOX_DEVELOP', '') == '1':
        freedombox_develop = True
        idle_shutdown_time = 5
        logger.info('Running development mode, idle shutdown time = %ss',
                    idle_shutdown_time)

    # When invoked as a systemd service, don't perform automatic idle shutdown.
    if not systemd.daemon.listen_fds(unset_environment=False):
        idle_shutdown_time = None

    module_loader.load_modules()
    app_module.apps_init()

    with Server(str(address), RequestHandler) as server:
        # systemd will wait until notification to proceed with other processes.
        # We have service Type=notify.
        systemd.daemon.notify('READY=1')

        try:
            server.serve_forever()
        except TimeoutError:
            logger.info('FreedomBox privileged daemon exiting on idle.')
        except Exception as exception:
            logger.exception(
                'FreedomBox privileged daemon exiting on error - %s',
                exception)
            sys.exit(-1)
        else:
            logger.info('FreedomBox privileged daemon exiting.')


if __name__ == '__main__':
    main()
