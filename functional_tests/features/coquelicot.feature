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

@apps @coquelicot @backups
Feature: Coquelicot File Sharing
  Run Coquelicot File Sharing server.

Background:
  Given I'm a logged in user
  Given the coquelicot application is installed

Scenario: Enable coquelicot application
  Given the coquelicot application is disabled
  When I enable the coquelicot application
  Then the coquelicot service should be running

Scenario: Disable coquelicot application
  Given the coquelicot application is enabled
  When I disable the coquelicot application
  Then the coquelicot service should not be running

Scenario: Modify maximum upload size
  Given the coquelicot application is enabled
  When I modify the maximum file size of coquelicot to 256
  Then the maximum file size of coquelicot should be 256

Scenario: Modify upload password
  Given the coquelicot application is enabled
  When I modify the coquelicot upload password to whatever123
  Then I should be able to login to coquelicot with password whatever123

Scenario: Modify maximum upload size in disabled case
  Given the coquelicot application is disabled
  When I modify the maximum file size of coquelicot to 123
  Then the coquelicot service should not be running

Scenario: Backup and restore coquelicot
  Given the coquelicot application is enabled
  When I modify the coquelicot upload password to beforebackup123
  And I modify the maximum file size of coquelicot to 128
  And I create a backup of the coquelicot app data
  And I export the coquelicot app data backup
  And I modify the coquelicot upload password to afterbackup123
  And I modify the maximum file size of coquelicot to 64
  And I restore the coquelicot app data backup
  Then the coquelicot service should be running
  And I should be able to login to coquelicot with password beforebackup123
  And the maximum file size of coquelicot should be 128
