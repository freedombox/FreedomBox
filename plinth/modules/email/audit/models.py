# SPDX-License-Identifier: AGPL-3.0-or-later
"""Models of the audit module"""

import logging

logger = logging.getLogger(__name__)


class UnresolvedIssueError(AssertionError):
    pass


class Diagnosis:
    """Records a diagnosis: what went wrong and how to fix them"""

    def __init__(self, title='', action=''):
        """Class constructor"""
        self.title = title
        self.action = action
        self.critical_errors = []
        self.errors = []

    def to_json(self):
        """Serialize object to JSON"""
        return {
            'class': self.__class__.__name__,
            'title': self.title,
            'action': self.action,
            'errors': self.errors,
            'critical_errors': self.critical_errors
        }

    @classmethod
    def from_json(cls, valid_dict, translate=None):
        """Construct a Diagnosis instance from a valid JSON dictionary.

        :type valid_dict: dict
        :param valid_dict: a valid dictionary representation
        :type translate: str -> Union[str, None]
        :param translate: optional; if specified, should be a function that
          accepts the title and returns a new title or None.
        """
        title = valid_dict['title']
        if translate:
            title = translate(title) or title
        result = cls(title, action=valid_dict['action'])
        result.errors.extend(valid_dict['errors'])
        result.critical_errors.extend(valid_dict['critical_errors'])
        return result

    def critical(self, message_fmt, *args):
        """Append a message to the critical errors list"""
        if args:
            self.critical_errors.append(message_fmt % args)
        else:
            self.critical_errors.append(message_fmt)

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

        if self.critical_errors:
            return [self.title, 'error']
        elif self.errors:
            return [self.title, 'failed']
        else:
            return [self.title, 'passed']

    @property
    def has_failed(self):
        """True if the diagnosis has failed or contains an error"""
        return (self.critical_errors or self.errors)

    def write_logs(self):
        """Log errors and failures"""
        logger.debug('Ran audit: %s', self.title)
        for message in self.critical_errors:
            logger.critical(message)
        for message in self.errors:
            logger.error(message)

    def sorting_key(self):
        """The key function for list.sort"""
        return (-len(self.critical_errors), -len(self.errors), self.title)


class MainCfDiagnosis(Diagnosis):
    """Diagnosis for a set of main.cf configuration keys"""

    def __init__(self, *args, **kwargs):
        """Class constructor. See :class:`.Diagnosis` for method signature"""
        super().__init__(*args, **kwargs)
        self.advice = {}
        self.user = {}

    def flag(self, key, corrected_value=None, user=None):
        """Flag a problematic key.

        If `corrected_value` is a str, the specified value is assumed to be
        correct.

        :type key: str
        :param key: main.cf key
        :type corrected_value: str or None
        :param corrected_value: corrected value
        :type user: Any
        :param user: customized data (see the :meth:`.repair` method)
        :raises ValueError: if the key has been flagged
        """
        if key in self.advice:
            raise ValueError('Key has been flagged')
        else:
            self.advice[key] = corrected_value
            self.user[key] = user

    def flag_once(self, key, **kwargs):
        """Flag a problematic key. If the key has been flagged, do nothing.

        See :meth:`.flag` for the function signature.
        """
        if key not in self.advice:
            self.flag(key, **kwargs)

    def unresolved_issues(self):
        """Return the iterator of all keys that do not have a corrected value.

        :return: an iterator of keys
        """
        for key, value in self.advice.items():
            if value is None:
                yield key

    def _compare_and_advise(self, current, default):
        if len(current) > len(default):
            raise ValueError('Sanity check failed: dictionary sizes')
        for key, value in default.items():
            if current.get(key, None) != value:
                self.flag(key, corrected_value=value)
                self.critical('%s must equal %s', key, value)

    def compare(self, expected, getter):
        """Check the current Postfix configuration. Flag and correct all keys
        that have an unexpected value.

        :type expected: dict[str, str]
        :param expected: a dictionary specifying the set of keys to be checked
          and their expected values
        :type getter: Iterator[str] -> dict[str, str]
        :param getter: a function that fetches the current postfix config; it
          takes an iterator of strings and returns a str-to-str dictionary.
        """
        current = getter(expected.keys())
        self._compare_and_advise(current, expected)

    def repair(self, key, repair_function):
        """Repair the key if its value has not been corrected by other means.

        `repair_function` will not be called if the key has had a corrected
        value or the key does not need attention.

        In case `repair_function` is called, we will pass in the `user` data
        associated with `key`.

        The job of `repair_function` is to return a corrected value. It should
        not modify any Postfix configuration in any way. It may read
        configuration files, but pending Postconf changes are not visible.

        If `repair_function` could not solve the problem, it may return `None`
        as an alternative to raising an exception. Using this feature, you may
        implement fallback strategies.

        :type key: str
        :param key: the key to be repaired
        :type repair_function: Any -> Union[str, None]
        :param repair_function: a function that returns the corrected value
          for `key`
        """
        if key in self.advice and self.advice[key] is None:
            self.advice[key] = repair_function(self.user[key])

    def apply_changes(self, setter):
        """Apply changes by calling the `setter` with a dictionary of corrected
        keys and values.

        :type setter: dict[str, str] -> None
        :param setter: configuration changing function that takes a str-to-str
          dictionary.
        :raises UnresolvedIssueError: if the diagnosis contains an uncorrected
          key
        """
        self.assert_resolved()
        logger.info('Setting postconf: %r', self.advice)
        setter(self.advice)

    def assert_resolved(self):
        """Raises an :class:`.UnresolvedIssueError` if the diagnosis report
        contains an unresolved issue (i.e. an uncorrected key)"""
        if None in self.advice.values():
            raise UnresolvedIssueError('Assertion failed')
