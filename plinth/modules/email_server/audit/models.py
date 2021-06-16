"""Audit models"""
# SPDX-License-Identifier: AGPL-3.0-or-later
import logging

logger = logging.getLogger(__name__)


class Result:
    def __init__(self, title):
        self.title = title
        self.fails = []
        self.errors = []

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
        logger.debug('Ran audit: ' + self.title)
        for message in self.errors:
            logger.critical(message)
        for message in self.fails:
            logger.error(message)
