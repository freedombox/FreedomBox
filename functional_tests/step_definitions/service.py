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

from pytest_bdd import parsers, then

from support import service
from support.service import eventually


@then(parsers.parse('the {service_name:w} service should be running'))
def service_should_be_running(browser, service_name):
    assert eventually(service.is_running, args=[browser, service_name])


@then(parsers.parse('the {service_name:w} service should not be running'))
def service_should_not_be_running(browser, service_name):
    assert eventually(service.is_not_running, args=[browser, service_name])


@then(parsers.parse('the network time service should be running'))
def ntp_should_be_running(browser):
    assert service.is_running(browser, 'ntp')


@then(parsers.parse('the network time service should not be running'))
def ntp_should_not_be_running(browser):
    assert not service.is_running(browser, 'ntp')


@then(parsers.parse('the service discovery service should be running'))
def avahi_should_be_running(browser):
    assert service.is_running(browser, 'avahi')


@then(parsers.parse('the service discovery service should not be running'))
def avahi_should_not_be_running(browser):
    assert not service.is_running(browser, 'avahi')
