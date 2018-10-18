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

@security @essential
Feature: Security
  Configure security options.

Background:
  Given I'm a logged in user

Scenario: Enable restricted console logins
  Given restricted console logins are disabled
  When I enable restricted console logins
  Then restricted console logins should be enabled

Scenario: Disable restricted console logins
  Given restricted console logins are enabled
  When I disable restricted console logins
  Then restricted console logins should be disabled

Scenario: Backup and restore security
  When I enable restricted console logins
  And I create a backup of the security app data
  And I disable restricted console logins
  And I export the security app data backup
  And I restore the security app data backup
  Then restricted console logins should be enabled
