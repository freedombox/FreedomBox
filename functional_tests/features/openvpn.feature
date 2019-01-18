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

@apps @openvpn @backups
Feature: OpenVPN - Virtual Private Network
  Setup and configure OpenVPN

Background:
  Given I'm a logged in user
  Given the openvpn application is installed
  Given the openvpn application is setup

Scenario: Enable openvpn application
  Given the openvpn application is disabled
  When I enable the openvpn application
  Then the openvpn service should be running

Scenario: Download openvpn profile
  Given the openvpn application is enabled
  Then the openvpn profile should be downloadable

Scenario: Backup and restore openvpn
  Given the openvpn application is enabled
  And I download openvpn profile
  When I create a backup of the openvpn app data
  And I restore the openvpn app data backup
  Then the openvpn profile downloaded should be same as before

Scenario: Disable openvpn application
  Given the openvpn application is enabled
  When I disable the openvpn application
  Then the openvpn service should not be running
