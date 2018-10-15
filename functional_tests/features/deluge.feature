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

@apps @deluge
Feature: Deluge BitTorrent Client
  Run the Deluge BitTorrent client.

Background:
  Given I'm a logged in user
  Given the deluge application is installed

Scenario: Enable deluge application
  Given the deluge application is disabled
  When I enable the deluge application
  Then the deluge site should be available

Scenario: Disable deluge application
  Given the deluge application is enabled
  When I disable the deluge application
  Then the deluge site should not be available

Scenario: Upload a torrent to deluge
  Given the deluge application is enabled
  When all torrents are removed from deluge
  And I upload a sample torrent to deluge
  Then there should be 1 torrents listed in deluge
