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

@sso @essential @system
Feature: Single Sign On
  Test Single Sign On features.

Background:
  Given I'm a logged in user
  Given the syncthing application is installed
  Given the syncthing application is enabled


Scenario: Logged out Plinth user cannot access Syncthing web interface
  Given I'm a logged out user
  When I access syncthing application
  Then I should be prompted for login

Scenario: Logged in Plinth user can access Syncthing web interface
  When I access syncthing application
  Then the syncthing site should be available
