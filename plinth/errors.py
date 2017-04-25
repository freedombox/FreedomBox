#
# This file is part of Plinth.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""
Project specific errors
"""


class PlinthError(Exception):
    """Base class for all Plinth specific errors."""
    pass


class ActionError(PlinthError):
    """Use this error for exceptions when executing an action."""
    pass


class DomainRegistrationError(PlinthError):
    """Domain registration failed"""
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
