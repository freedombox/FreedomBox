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

@apps @syncthing @sso @backups
Feature: Syncthing File Synchronization
  Run Syncthing File Synchronization server.

Background:
  Given I'm a logged in user
  Given the syncthing application is installed

Scenario: Enable syncthing application
  Given the syncthing application is disabled
  When I enable the syncthing application
  Then the syncthing service should be running

Scenario: Add a syncthing folder
  Given the syncthing application is enabled
  And syncthing folder Test is not present
  When I add a folder /tmp as syncthing folder Test
  Then syncthing folder Test should be present

Scenario: Remove a syncthing folder
  Given the syncthing application is enabled
  And folder /tmp is present as syncthing folder Test
  When I remove syncthing folder Test
  Then syncthing folder Test should not be present

Scenario: Backup and restore syncthing
  Given the syncthing application is enabled
  And syncthing folder Test is not present
  When I add a folder /tmp as syncthing folder Test
  And I create a backup of the syncthing app data
  And I remove syncthing folder Test
  And I restore the syncthing app data backup
  Then syncthing folder Test should be present

Scenario: Disable syncthing application
  Given the syncthing application is enabled
  When I disable the syncthing application
  Then the syncthing service should not be running
