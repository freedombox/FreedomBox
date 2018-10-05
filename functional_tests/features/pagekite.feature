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

@apps @pagekite
Feature: Pagekite Public Visibility
  Configure Pagekite public visitbility server.

Background:
  Given I'm a logged in user
  Given the pagekite application is installed

Scenario: Enable pagekite application
  Given pagekite is disabled
  When I enable pagekite
  Then pagekite should be enabled

Scenario: Disable pagekite application
  Given pagekite is enabled
  When I disable pagekite
  Then pagekite should be disabled

Scenario: Configure pagekite application
  Given pagekite is enabled
  When I configure pagekite with host pagekite.example.com, port 8080, kite name mykite.example.com and kite secret mysecret
  Then pagekite should be configured with host pagekite.example.com, port 8080, kite name mykite.example.com and kite secret mysecret
