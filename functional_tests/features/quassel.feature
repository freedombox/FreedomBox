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

@apps @quassel @backups
Feature: Quassel IRC Client
  Run Quassel core.

Background:
  Given I'm a logged in user
  Given the quassel application is installed

Scenario: Enable quassel application
  Given the quassel application is disabled
  When I enable the quassel application
  Then the quassel service should be running

# TODO: Improve this to actually check that data configured servers is restored.
Scenario: Backup and restore quassel
  Given the quassel application is enabled
  When I create a backup of the quassel app data
  And I restore the quassel app data backup
  Then the quassel service should be running

Scenario: Disable quassel application
  Given the quassel application is enabled
  When I disable the quassel application
  Then the quassel service should not be running
