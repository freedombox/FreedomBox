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

@apps @mldonkey @sso
Feature: MLDonkey eDonkey Network Client
  Run the eDonkey Network client.

Background:
  Given I'm a logged in user
  Given the mldonkey application is installed

Scenario: Enable mldonkey application
  Given the mldonkey application is disabled
  When I enable the mldonkey application
  Then the mldonkey site should be available

Scenario: Disable mldonkey application
  Given the mldonkey application is enabled
  When I disable the mldonkey application
  Then the mldonkey site should not be available

# Scenario: Upload an ed2k file to mldonkey
#   Given the mldonkey application is enabled
#   When all ed2k files are removed from mldonkey
#   And I upload a sample ed2k file to mldonkey
#   Then there should be 1 ed2k file listed in mldonkey
#
# Scenario: Backup and restore mldonkey
#   Given the mldonkey application is enabled
#   When all ed2k files are removed from mldonkey
#   And I upload a sample ed2k file to mldonkey
#   And I create a backup of the mldonkey app data
#   And all ed2k files are removed from mldonkey
#   And I restore the mldonkey app data backup
#   Then the mldonkey service should be running
#   And there should be 1 torrents listed in mldonkey
