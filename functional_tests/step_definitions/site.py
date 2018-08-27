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


@when(
    parsers.parse(
        'I upload an image named {image:S} to mediawiki with credentials {username:w} and '
        '{password:w}'))
def upload_image(browser, username, password, image):
    site.upload_image_mediawiki(browser, username, password, image)


@then(parsers.parse('there should be {image:S} image'))
def uploaded_image_should_be_available(browser, image):
    uploaded_image = site.get_uploaded_image_in_mediawiki(browser, image)
    assert image.lower() == uploaded_image.lower()


@then(
    parsers.parse(
        'I should be able to login to coquelicot with password {password:w}'))
def verify_upload_password(browser, password):
    site.verify_coquelicot_upload_password(browser, password)


@then(parsers.parse('the mediawiki site should allow creating accounts'))
def mediawiki_allows_creating_accounts(browser):
    site.verify_mediawiki_create_account_link(browser)


@then(parsers.parse('the mediawiki site should not allow creating accounts'))
def mediawiki_does_not_allow_creating_accounts(browser):
    site.verify_mediawiki_no_create_account_link(browser)


@then(
    parsers.parse('the mediawiki site should allow anonymous reads and writes')
)
def mediawiki_allows_anonymous_reads_edits(browser):
    site.verify_mediawiki_anonymous_reads_edits_link(browser)


@then(
    parsers.parse(
        'the mediawiki site should not allow anonymous reads and writes'))
def mediawiki_does_not_allow__account_creation_anonymous_reads_edits(browser):
    site.verify_mediawiki_no_anonymous_reads_edits_link(browser)


@then(
    parsers.parse(
        'I should see the Upload File option in the side pane when logged in '
        'with credentials {username:w} and {password:w}'))
def login_to_mediawiki_with_credentials(browser, username, password):
    site.login_to_mediawiki_with_credentials(browser, username, password)
