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

@apps @transmission
Feature: BitTorrent Client
  Run the Transmission BitTorrent client.

Background:
  Given I'm a logged in user
  Given the transmission application is installed

Scenario: Enable transmission application
  Given the transmission application is disabled
  When I enable the transmission application
  Then the transmission site should be available

Scenario: Disable transmission application
  Given the transmission application is enabled
  When I disable the transmission application
  Then the transmission site should not be available
