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

from pytest_bdd import given, parsers, then, when

from support import application


@given(parsers.parse('the {app_name:w} application is installed'))
def application_is_installed(browser, app_name):
    application.install(browser, app_name)


@given(parsers.parse('the {app_name:w} application is enabled'))
def application_is_enabled(browser, app_name):
    application.enable(browser, app_name)


@given(parsers.parse('the {app_name:w} application is disabled'))
def application_is_disabled(browser, app_name):
    application.disable(browser, app_name)


@given(parsers.parse('the network time application is enabled'))
def ntp_is_enabled(browser):
    application.enable(browser, 'ntp')


@given(parsers.parse('the network time application is disabled'))
def ntp_is_disabled(browser):
    application.disable(browser, 'ntp')


@given(parsers.parse('the service discovery application is enabled'))
def avahi_is_enabled(browser):
    application.enable(browser, 'avahi')


@given(parsers.parse('the service discovery application is disabled'))
def avahi_is_disabled(browser):
    application.disable(browser, 'avahi')


@when(parsers.parse('I enable the {app_name:w} application'))
def enable_application(browser, app_name):
    application.enable(browser, app_name)


@when(parsers.parse('I disable the {app_name:w} application'))
def disable_application(browser, app_name):
    application.disable(browser, app_name)


@when(parsers.parse('I enable the network time application'))
def enable_ntp(browser):
    application.enable(browser, 'ntp')


@when(parsers.parse('I disable the network time application'))
def disable_ntp(browser):
    application.disable(browser, 'ntp')


@when(parsers.parse('I enable the service discovery application'))
def enable_avahi(browser):
    application.enable(browser, 'avahi')


@when(parsers.parse('I disable the service discovery application'))
def disable_avahi(browser):
    application.disable(browser, 'avahi')


@given(
    parsers.parse('the domain name for {app_name:w} is set to {domain_name:w}')
)
def select_domain_name(browser, app_name, domain_name):
    application.select_domain_name(browser, app_name, domain_name)


@given('the shadowsocks application is configured')
def configure_shadowsocks(browser):
    application.configure_shadowsocks(browser)


@when(
    parsers.parse('I modify the maximum file size of coquelicot to {size:d}'))
def modify_max_file_size(browser, size):
    application.modify_max_file_size(browser, size)


@then(parsers.parse('the maximum file size of coquelicot should be {size:d}'))
def assert_max_file_size(browser, size):
    assert application.get_max_file_size(browser) == size


@when(parsers.parse('I modify the coquelicot upload password to {password:w}'))
def modify_upload_password(browser, password):
    application.modify_upload_password(browser, password)
