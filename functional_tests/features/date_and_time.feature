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

@essential @date-and-time @system @backups
Feature: Date and Time
  Configure time zone and network time service.

Background:
  Given I'm a logged in user

Scenario: Disable network time application
  Given the network time application is enabled
  When I disable the network time application
  Then the network time service should not be running

Scenario: Enable network time application
  Given the network time application is disabled
  When I enable the network time application
  Then the network time service should be running

Scenario: Set timezone
  When I set the time zone to Africa/Abidjan
  Then the time zone should be Africa/Abidjan

Scenario: Backup and restore datetime
  When I set the time zone to Africa/Accra
  And I create a backup of the datetime app data
  And I set the time zone to Africa/Cairo
  And I restore the datetime app data backup
  Then the time zone should be Africa/Accra
