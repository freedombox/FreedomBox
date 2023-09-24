# SPDX-License-Identifier: AGPL-3.0-or-later
"""Utilities to run operations and show their progress or failures."""

import enum
import logging
import threading
from typing import Callable, Optional

from . import app as app_module

logger = logging.getLogger(__name__)


class Operation:
    """Represent an ongoing or finished activity."""

    class State(enum.Enum):
        """Various states of an operation."""

        WAITING: str = 'waiting'
        RUNNING: str = 'running'
        COMPLETED: str = 'completed'

    def __init__(self, app_id: str, name: str, target: Callable,
                 args: Optional[list] = None, kwargs: Optional[dict] = None,
                 show_message: bool = True, show_notification: bool = False,
                 thread_data: Optional[dict] = None,
                 on_complete: Callable = None):
        """Initialize to no operation."""
        self.app_id = app_id
        self.name = name
        self.show_message = show_message
        self.show_notification = show_notification

        self.target = target
        self.args = args or []
        self.kwargs = kwargs or {}
        self.on_complete = on_complete

        self.state = Operation.State.WAITING
        self.return_value = None
        self._message: Optional[str] = None
        self.exception: Optional[Exception] = None

        # Operation specific data
        self.thread_data: dict = thread_data or {}

        self.thread = threading.Thread(target=self._catch_thread_errors)
        self.start_event = threading.Event()
        setattr(self.thread, '_operation', self)
        self._update_notification()

    def __str__(self):
        """Return a string representation of the operation."""
        return f'Operation: {self.app_id}: {self.name}'

    def _catch_thread_errors(self):
        """Collect exceptions when running in a thread."""
        self._update_notification()
        try:
            self.return_value = self.target(*self.args, **self.kwargs)
        except Exception as exception:
            logger.exception('Error: %s, %s', self, exception)
            self.exception = exception
        finally:
            self.state = Operation.State.COMPLETED
            self._update_notification()
            # Notify
            if self.on_complete:
                self.on_complete(self)

    def run(self):
        """Run a specified operation in a thread."""
        logger.info('%s: running', str(self))
        self.state = Operation.State.RUNNING
        self.thread.start()
        self.start_event.set()

    def join(self):
        """Block the current thread until the operation is completed.

        Raise an exception if the thread encountered an exception.
        """
        self.start_event.wait()
        self.thread.join()
        if self.exception:
            raise self.exception

        return self.return_value

    @staticmethod
    def get_operation() -> 'Operation':
        """Return the operation associated with this thread."""
        thread = threading.current_thread()
        return thread._operation  # type: ignore [attr-defined]

    def on_update(self, message: Optional[str] = None,
                  exception: Optional[Exception] = None):
        """Call from within the thread to update the progress of operation."""
        if message:
            self._message = message

        if exception:
            self.exception = exception

        self._update_notification()

    @property
    def message(self) -> str | None:
        """Return a message about status of the operation."""
        from django.utils.translation import gettext_noop
        if self._message:  # Progress has been set by the operation itself
            return self._message

        if self.exception:  # Operation resulted in a error.
            return gettext_noop('Error: {name}: {exception_message}')

        if self.state == Operation.State.WAITING:
            return gettext_noop('Waiting to start: {name}')

        if self.state == Operation.State.RUNNING:
            return '{name}'  # No translation needed

        if self.state == Operation.State.COMPLETED:
            return gettext_noop('Finished: {name}')

        return None

    @property
    def translated_message(self):
        """Return a message about status of operation after translating.

        Must be called from a web request (UI) thread with user language set so
        that localization is done properly.
        """
        from django.utils.translation import gettext
        message = gettext(self.message)
        message = message.format(name=self.name,
                                 exception_message=str(self.exception))
        if self.app_id:
            message = message.format(
                app_name=app_module.App.get(self.app_id).info.name)

        return message

    def _update_notification(self):
        """Show an updated notification if needed."""
        if not self.show_notification:
            return

        from plinth.notification import Notification
        severity = 'info' if not self.exception else 'error'
        app = app_module.App.get(self.app_id)
        data = {
            'app_name': str(app.info.name),
            'app_icon': app.info.icon,
            'app_icon_filename': app.info.icon_filename,
            'state': self.state.value,
            'exception': str(self.exception) if self.exception else None,
            'name': 'translate:' + str(self.name),
        }
        Notification.update_or_create(
            id=self.app_id + '-operation', app_id=self.app_id,
            severity=severity, title=app.info.name, message=self.message,
            body_template='operation-notification.html', data=data,
            group='admin', dismissed=False)


class OperationsManager:
    """Global handler for all operations and their results."""

    def __init__(self):
        """Initialize the object."""
        self._operations: list[Operation] = []
        self._current_operation: Optional[Operation] = None

        # Assume that operations manager will be called from various threads
        # including the callback called from the threads it creates. Ensure
        # that properties don't get corrupted due to race conditions when
        # called from different threads by locking all code that updates them.
        # It is re-entrant lock, meaning it can be re-obtained without blocking
        # when done from the same thread which holds the lock.
        self._lock = threading.RLock()

    def new(self, *args, **kwargs):
        """Create a new operation instance and add to global list."""
        with self._lock:
            kwargs['on_complete'] = self._on_operation_complete
            operation = Operation(*args, **kwargs)
            self._operations.append(operation)
            logger.info('%s: added', operation)
            self._schedule_next()
            return operation

    def _on_operation_complete(self, operation):
        """Trigger next operation. Called from within previous thread."""
        logger.debug('%s: on_complete called', operation)
        with self._lock:
            self._current_operation = None
            if not operation.show_message:
                # No need to keep it lingering for later collection
                self._operations.remove(operation)

            self._schedule_next()

    def _schedule_next(self):
        """Schedule the next available operation."""
        with self._lock:
            if self._current_operation:
                return

            for operation in self._operations:
                if operation.state == Operation.State.WAITING:
                    logger.debug('%s: scheduling', operation)
                    self._current_operation = operation
                    operation.run()
                    break

    def filter(self, app_id):
        """Return operations matching a pattern."""
        with self._lock:
            return [
                operation for operation in self._operations
                if operation.app_id == app_id
            ]

    def collect_results(self, app_id):
        """Return the finished operations for an app."""
        results: list[Operation] = []
        remaining: list[Operation] = []

        with self._lock:
            for operation in self._operations:
                if (operation.app_id == app_id
                        and operation.state == Operation.State.COMPLETED):
                    results.append(operation)
                else:
                    remaining.append(operation)

            if results:
                self._operations = remaining

        return results


manager = OperationsManager()
