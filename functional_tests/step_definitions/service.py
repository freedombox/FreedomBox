# SPDX-License-Identifier: AGPL-3.0-or-later

from pytest_bdd import parsers, then

from support import service
from support.service import eventually


@then(parsers.parse('the {service_name:w} service should be running'))
def service_should_be_running(session_browser, service_name):
    assert eventually(service.is_running, args=[session_browser, service_name])


@then(parsers.parse('the {service_name:w} service should not be running'))
def service_should_not_be_running(session_browser, service_name):
    assert eventually(service.is_not_running,
                      args=[session_browser, service_name])


@then(parsers.parse('the network time service should be running'))
def ntp_should_be_running(session_browser):
    assert service.is_running(session_browser, 'ntp')


@then(parsers.parse('the network time service should not be running'))
def ntp_should_not_be_running(session_browser):
    assert not service.is_running(session_browser, 'ntp')


@then(parsers.parse('the service discovery service should be running'))
def avahi_should_be_running(session_browser):
    assert service.is_running(session_browser, 'avahi')


@then(parsers.parse('the service discovery service should not be running'))
def avahi_should_not_be_running(session_browser):
    assert not service.is_running(session_browser, 'avahi')
