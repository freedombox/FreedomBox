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

from pytest_bdd import parsers, then, when

from support import site


@then(parsers.parse('the {site_name:w} site should be available'))
def site_should_be_available(browser, site_name):
    assert site.is_available(browser, site_name)


@then(parsers.parse('the {site_name:w} site should not be available'))
def site_should_not_be_available(browser, site_name):
    assert not site.is_available(browser, site_name)


@when(parsers.parse('I access {app_name:w} application'))
def access_application(browser, app_name):
    site.access_url(browser, app_name)


@then(
    parsers.parse(
        'I should be able to login to coquelicot with password {password:w}'))
def verify_upload_password(browser, password):
    site.verify_coquelicot_upload_password(browser, password)
