# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Project specific errors
"""


class PlinthError(Exception):
    """Base class for all FreedomBox specific errors."""
    pass


class ActionError(PlinthError):
    """Use this error for exceptions when executing an action."""
    pass


class PackageNotInstalledError(PlinthError):
    """Could not complete module setup due to missing package."""
    pass


class DomainNotRegisteredError(PlinthError):
    """
    An action couldn't be performed because this
    FreedomBox doesn't have a registered domain
    """
    pass


class MissingPackageError(PlinthError):
    """Package is not available to be installed at this time."""

    def __init__(self, name):
        self.name = name
        super().__init__(self.name)
