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

@apps @tor
Feature: Tor Anonymity Network
  Manage Tor configuration.

Background:
  Given I'm a logged in user
  Given the tor application is installed

Scenario: Enable tor application
  Given the tor application is disabled
  When I enable the tor application
  Then the tor service should be running

Scenario: Disable tor application
  Given the tor application is enabled
  When I disable the tor application
  Then the tor service should not be running
