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

@apps @searx @backups @sso
Feature: Searx Web Search
  Run Searx metasearch engine.

Background:
  Given I'm a logged in user
  Given the searx application is installed

Scenario: Enable searx application
  Given the searx application is disabled
  When I enable the searx application
  Then the searx site should be available

Scenario: Disable searx application
  Given the searx application is enabled
  When I disable the searx application
  Then the searx site should not be available

Scenario: Backup and restore searx
  Given the searx application is enabled
  When I create a backup of the searx app data
  And I restore the searx app data backup
  Then the searx site should be available
