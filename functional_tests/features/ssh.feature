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

@apps @ssh @backups
Feature: Secure Shell Server
  Run secure shell server.

Background:
  Given I'm a logged in user
  Given the ssh application is installed

Scenario: Enable ssh application
  Given the ssh application is disabled
  When I enable the ssh application
  Then the ssh service should be running

Scenario: Disable ssh application
  Given the ssh application is enabled
  When I disable the ssh application
  Then the ssh service should not be running

# TODO: Improve this to actually check that earlier ssh certificate has been
# restored.
Scenario: Backup and restore ssh
  Given the ssh application is enabled
  When I create a backup of the ssh app data
  And I export the ssh app data backup
  And I restore the ssh app data backup
  Then the ssh service should be running
