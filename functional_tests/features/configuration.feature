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

@system @essential @configuration
Feature: Configuration
  Configure the system.

Background:
  Given I'm a logged in user

Scenario: Change hostname
  When I change the hostname to mybox
  Then the hostname should be mybox

Scenario: Change domain name
  When I change the domain name to mydomain.example
  Then the domain name should be mydomain.example

Scenario: Change webserver home page
  Given the syncthing application is installed
  And the syncthing application is enabled
  And the home page is syncthing
  When I change the home page to plinth
  Then the home page should be plinth

