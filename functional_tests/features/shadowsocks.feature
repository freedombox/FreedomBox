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

@apps @shadowsocks @backups
Feature: Shadowsocks Socks5 Proxy
  Run the Shadowsocks Socks5 proxy client.

Background:
  Given I'm a logged in user
  Given the shadowsocks application is installed
  Given the shadowsocks application is configured

Scenario: Enable shadowsocks application
  Given the shadowsocks application is disabled
  When I enable the shadowsocks application
  Then the shadowsocks service should be running

Scenario: Disable shadowsocks application
  Given the shadowsocks application is enabled
  When I disable the shadowsocks application
  Then the shadowsocks service should not be running

Scenario: Backup and restore shadowsocks
  Given the shadowsocks application is enabled
  When I configure shadowsocks with server beforebackup.example.com and password beforebackup123
  And I create a backup of the shadowsocks app data
  And I configure shadowsocks with server afterbackup.example.com and password afterbackup123
  And I export the shadowsocks app data backup
  And I restore the shadowsocks app data backup
  Then the shadowsocks service should be running
  And shadowsocks should be configured with server beforebackup.example.com and password beforebackup123
