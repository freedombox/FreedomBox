#
# This file is part of FreedomBox.
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

@apps @radicale
Feature: Radicale Calendar and Addressbook
  Configure CalDAV/CardDAV server.

Background:
  Given I'm a logged in user
  Given the radicale application is installed

Scenario: Enable radicale application
  Given the radicale application is disabled
  When I enable the radicale application
  Then the radicale service should be running
  And the calendar should be available
  And the addressbook should be available

Scenario: Disable radicale application
  Given the radicale application is enabled
  When I disable the radicale application
  Then the radicale service should not be running
  And the calendar should not be available
  And the addressbook should not be available

Scenario: Owner-only access rights
  Given the radicale application is enabled
  And the access rights are set to "any user can view, but only the owner can make changes"
  When I change the access rights to "only the owner can view or make changes"
  Then the radicale service should be running
  And the access rights should be "only the owner can view or make changes"

Scenario: Owner-write access rights
  Given the radicale application is enabled
  And the access rights are set to "only the owner can view or make changes"
  When I change the access rights to "any user can view, but only the owner can make changes"
  Then the radicale service should be running
  And the access rights should be "any user can view, but only the owner can make changes"

Scenario: Authenticated access rights
  Given the radicale application is enabled
  And the access rights are set to "only the owner can view or make changes"
  When I change the access rights to "any user can view or make changes"
  Then the radicale service should be running
  And the access rights should be "any user can view or make changes"
