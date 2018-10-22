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

@apps @jsxc @backups
Feature: JSXC XMPP Client
  Run the JSXC XMPP client.

Background:
  Given I'm a logged in user

Scenario: Install jsxc application
  Given the jsxc application is installed
  Then the jsxc site should be available

Scenario: Backup and restore jsxc
  Given the jsxc application is installed
  When I create a backup of the jsxc app data
  And I restore the jsxc app data backup
  Then the jsxc site should be available
