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

from support import config, interface

default_url = config['DEFAULT']['url']


@given("I'm a logged in user")
def logged_in_user(session_browser):
    interface.login(session_browser, default_url,
                    config['DEFAULT']['username'],
                    config['DEFAULT']['password'])


@given("I'm a logged out user")
def logged_out_user(session_browser):
    session_browser.visit(default_url + '/plinth/accounts/logout/')


@when("I log out")
def log_out_user(session_browser):
    session_browser.visit(default_url + '/plinth/accounts/logout/')


@then(parsers.parse('I should be prompted for login'))
def prompted_for_login(session_browser):
    assert interface.is_login_prompt(session_browser)


@given(parsers.parse("the user {name:w} doesn't exist"))
def new_user_does_not_exist(session_browser, name):
    interface.delete_user(session_browser, name)


@given(parsers.parse('the user {name:w} exists'))
def test_user_exists(session_browser, name):
    interface.nav_to_module(session_browser, 'users')
    user_link = session_browser.find_link_by_href('/plinth/sys/users/' + name +
                                                  '/edit/')
    if not user_link:
        create_user(session_browser, name, 'secret123')


@when(
    parsers.parse('I create a user named {name:w} with password {password:w}'))
def create_user(session_browser, name, password):
    interface.create_user(session_browser, name, password)


@when(parsers.parse('I rename the user {old_name:w} to {new_name:w}'))
def rename_user(session_browser, old_name, new_name):
    interface.rename_user(session_browser, old_name, new_name)


@when(parsers.parse('I delete the user {name:w}'))
def delete_user(session_browser, name):
    interface.delete_user(session_browser, name)


@then(parsers.parse('{name:w} should be listed as a user'))
def new_user_is_listed(session_browser, name):
    assert interface.is_user(session_browser, name)


@then(parsers.parse('{name:w} should not be listed as a user'))
def new_user_is_not_listed(session_browser, name):
    assert not interface.is_user(session_browser, name)


@given('a sample local file')
def sample_local_file():
    file_path, contents = interface.create_sample_local_file()
    return dict(file_path=file_path, contents=contents)


@when('I go to the status logs page')
def help_go_to_status_logs(session_browser):
    interface.go_to_status_logs(session_browser)


@then('status logs should be shown')
def help_status_logs_are_shown(session_browser):
    assert interface.are_status_logs_shown(session_browser)


@given(parsers.parse("I'm on the {name:w} page"))
def go_to_module(session_browser, name):
    interface.nav_to_module(session_browser, name)
