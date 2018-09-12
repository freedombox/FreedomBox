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

@apps @ikiwiki @backups
Feature: ikiwiki Wiki and Blog
  Manage wikis and blogs.

Background:
  Given I'm a logged in user
  Given the wiki application is installed

Scenario: Enable wiki application
  Given the wiki application is disabled
  When I enable the wiki application
  Then the wiki site should be available

Scenario: Disable wiki application
  Given the wiki application is enabled
  When I disable the wiki application
  Then the wiki site should not be available

Scenario: Backup and restore wiki
  Given the wiki application is enabled
  When there is an ikiwiki wiki
  And I create a backup of the ikiwiki app data
  And I delete the ikiwiki wiki
  And I export the ikiwiki app data backup
  And I restore the ikiwiki app data backup
  Then the ikiwiki wiki should be restored
