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

@apps @dynamicdns @backups
Feature: Dynamic DNS Client
  Update public IP to a GnuDIP server.

Background:
  Given I'm a logged in user
  And the dynamicdns application is installed

Scenario: Backup and restore configuration
  Given dynamicdns is configured
  When I create a backup of the dynamicdns app data
  And I change the dynamicdns configuration
  And I restore the dynamicdns app data backup
  Then dynamicdns should have the original configuration
