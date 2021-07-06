"""Audit models"""
# SPDX-License-Identifier: AGPL-3.0-or-later
import logging

logger = logging.getLogger(__name__)


class UnresolvedIssueError(AssertionError):
    pass


class Diagnosis:
    def __init__(self, title):
        self.title = title
        self.fails = []
        self.errors = []

    def critical(self, message_fmt, *args):
        """Append a message to the fails list"""
        if args:
            self.fails.append(message_fmt % args)
        else:
            self.fails.append(message_fmt)

    def error(self, message_fmt, *args):
        """Append a message to the errors list"""
        if args:
            self.errors.append(message_fmt % args)
        else:
            self.errors.append(message_fmt)

    def summarize(self, log=True):
        """Return a 2-element list for the diagnose function in AppView"""
        if log:
            self.write_logs()

        if self.errors:
            return [self.title, 'error']
        elif self.fails:
            return [self.title, 'failed']
        else:
            return [self.title, 'passed']

    def write_logs(self):
        """Log errors and failures"""
        logger.debug('Ran audit: %s', self.title)
        for message in self.errors:
            logger.critical(message)
        for message in self.fails:
            logger.error(message)


class MainCfDiagnosis(Diagnosis):
    def __init__(self, title):
        super().__init__(title)
        self.advice = {}
        self.user = {}

    def flag(self, key, corrected_value=None, user=None):
        self.advice[key] = corrected_value
        self.user[key] = user

    def unresolved_issues(self):
        """Returns an interator of dictionary keys"""
        for key, value in self.advice.items():
            if value is None:
                yield key

    def compare_and_advise(self, current, default):
        if len(current) > len(default):
            raise ValueError('Sanity check failed: dictionary sizes')
        for key, value in default.items():
            if current.get(key, None) != value:
                self.flag(key, corrected_value=value)
                self.critical('%s must equal %s', key, value)

    def assert_resolved(self):
        """Raises an UnresolvedIssueError if the diagnosis report contains an
        unresolved issue"""
        if None in self.advice.values():
            raise UnresolvedIssueError('Assertion failed')
