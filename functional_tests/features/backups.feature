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

@backups
Feature: Backups module
  Create and restore backups.

Background:
  Given I'm a logged in user
  Given the bind application is installed

Scenario: Browser waits for redirect after restoring a backup
  Given the bind application is enabled
  When I create a backup of the bind app data
  And I restore the bind app data backup
  And I open the main page
  And I wait for 5 seconds
  Then the main page should be shown

Scenario: Download, upload and restore a backup
  Given the bind application is enabled
  When I set bind forwarders to 1.1.1.1
  And I create a backup of the bind app data
  And I set bind forwarders to 1.0.0.1
  And I download the latest app data backup
  And I restore the downloaded app data backup
  Then bind forwarders should be 1.1.1.1
