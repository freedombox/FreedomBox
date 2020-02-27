# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import os
import pathlib
import time

import requests
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from support import application, config, interface, system
from support.service import eventually, wait_for_page_update

# unlisted sites just use '/' + site_name as url
site_url = {
    'wiki': '/ikiwiki',
    'jsxc': '/plinth/apps/jsxc/jsxc/',
    'cockpit': '/_cockpit/',
    'syncthing': '/syncthing/',
}


def get_site_url(site_name):
    if site_name.startswith('share'):
        site_name = site_name.replace('_', '/')
    url = '/' + site_name
    if site_name in site_url:
        url = site_url[site_name]
    return url


def is_available(browser, site_name):
    url_to_visit = config['DEFAULT']['url'] + get_site_url(site_name)
    browser.visit(url_to_visit)
    time.sleep(3)
    browser.reload()
    not_404 = '404' not in browser.title
    # The site might have a default path after the sitename,
    # e.g /mediawiki/Main_Page
    no_redirect = browser.url.startswith(url_to_visit.strip('/'))
    return not_404 and no_redirect


def access_url(browser, site_name):
    browser.visit(config['DEFAULT']['url'] + get_site_url(site_name))


def verify_coquelicot_upload_password(browser, password):
    browser.visit(config['DEFAULT']['url'] + '/coquelicot')
    # ensure the password form is scrolled into view
    browser.execute_script('window.scrollTo(100, 0)')
    browser.find_by_id('upload_password').fill(password)
    actions = ActionChains(browser.driver)
    actions.send_keys(Keys.RETURN)
    actions.perform()
    assert eventually(browser.is_element_present_by_css,
                      args=['div[style*="display: none;"]'])


def upload_file_to_coquelicot(browser, file_path, password):
    """Upload a local file from disk to coquelicot."""
    verify_coquelicot_upload_password(browser, password)
    browser.attach_file('file', file_path)
    interface.submit(browser)
    assert eventually(browser.is_element_present_by_css,
                      args=['#content .url'])
    url_textarea = browser.find_by_css('#content .url textarea').first
    return url_textarea.value


def verify_mediawiki_create_account_link(browser):
    browser.visit(config['DEFAULT']['url'] +
                  '/mediawiki/index.php/Special:CreateAccount')
    assert eventually(browser.is_element_present_by_id,
                      args=['wpCreateaccount'])


def verify_mediawiki_no_create_account_link(browser):
    browser.visit(config['DEFAULT']['url'] +
                  '/mediawiki/index.php/Special:CreateAccount')
    assert eventually(browser.is_element_not_present_by_id,
                      args=['wpCreateaccount'])


def verify_mediawiki_anonymous_reads_edits_link(browser):
    browser.visit(config['DEFAULT']['url'] + '/mediawiki')
    assert eventually(browser.is_element_present_by_id, args=['ca-nstab-main'])


def verify_mediawiki_no_anonymous_reads_edits_link(browser):
    browser.visit(config['DEFAULT']['url'] + '/mediawiki')
    assert eventually(browser.is_element_not_present_by_id,
                      args=['ca-nstab-main'])
    assert eventually(browser.is_element_present_by_id,
                      args=['ca-nstab-special'])


def _login_to_mediawiki(browser, username, password):
    browser.visit(config['DEFAULT']['url'] +
                  '/mediawiki/index.php?title=Special:Login')
    browser.find_by_id('wpName1').fill(username)
    browser.find_by_id('wpPassword1').fill(password)
    with wait_for_page_update(browser):
        browser.find_by_id('wpLoginAttempt').click()


def login_to_mediawiki_with_credentials(browser, username, password):
    _login_to_mediawiki(browser, username, password)
    # Had to put it in the same step because sessions don't
    # persist between steps
    assert eventually(browser.is_element_present_by_id, args=['t-upload'])


def upload_image_mediawiki(browser, username, password, image):
    """Upload an image to MediaWiki. Idempotent."""
    browser.visit(config['DEFAULT']['url'] + '/mediawiki')
    _login_to_mediawiki(browser, username, password)

    # Upload file
    browser.visit(config['DEFAULT']['url'] + '/mediawiki/Special:Upload')
    file_path = pathlib.Path(__file__).parent
    file_path /= '../../static/themes/default/img/' + image
    browser.attach_file('wpUploadFile', str(file_path.resolve()))
    interface.submit(browser, element=browser.find_by_name('wpUpload')[0])


def get_number_of_uploaded_images_in_mediawiki(browser):
    browser.visit(config['DEFAULT']['url'] + '/mediawiki/Special:ListFiles')
    return len(browser.find_by_css('.TablePager_col_img_timestamp'))


def get_uploaded_image_in_mediawiki(browser, image):
    browser.visit(config['DEFAULT']['url'] + '/mediawiki/Special:ListFiles')
    elements = browser.find_link_by_partial_href(image)
    return elements[0].value


def mediawiki_delete_main_page(browser):
    """Delete the mediawiki main page."""
    _login_to_mediawiki(browser, 'admin', 'whatever123')
    browser.visit(
        '{}/mediawiki/index.php?title=Main_Page&action=delete'.format(
            interface.default_url))
    with wait_for_page_update(browser):
        browser.find_by_id('wpConfirmB').first.click()


def mediawiki_has_main_page(browser):
    """Check if mediawiki main page exists."""
    return eventually(_mediawiki_has_main_page, [browser])


def _mediawiki_has_main_page(browser):
    """Check if mediawiki main page exists."""
    browser.visit('{}/mediawiki/Main_Page'.format(interface.default_url))
    content = browser.find_by_id('mw-content-text').first
    return 'This page has been deleted.' not in content.text


def jsxc_login(browser):
    """Login to JSXC."""
    access_url(browser, 'jsxc')
    browser.find_by_id('jsxc-username').fill(config['DEFAULT']['username'])
    browser.find_by_id('jsxc-password').fill(config['DEFAULT']['password'])
    browser.find_by_id('jsxc-submit').click()
    relogin = browser.find_by_text('relogin')
    if relogin:
        relogin.first.click()
        browser.find_by_id('jsxc_username').fill(config['DEFAULT']['username'])
        browser.find_by_id('jsxc_password').fill(config['DEFAULT']['password'])
        browser.find_by_text('Connect').first.click()


def jsxc_add_contact(browser):
    """Add a contact to JSXC user's roster."""
    system.set_domain_name(browser, 'localhost')
    application.install(browser, 'jsxc')
    jsxc_login(browser)
    new = browser.find_by_text('new contact')
    if new:  # roster is empty
        new.first.click()
        browser.find_by_id('jsxc_username').fill('alice@localhost')
        browser.find_by_text('Add').first.click()


def jsxc_delete_contact(browser):
    """Delete the contact from JSXC user's roster."""
    jsxc_login(browser)
    browser.find_by_css('div.jsxc_more').first.click()
    browser.find_by_text('delete contact').first.click()
    browser.find_by_text('Remove').first.click()


def jsxc_has_contact(browser):
    """Check whether the contact is in JSXC user's roster."""
    jsxc_login(browser)
    contact = browser.find_by_text('alice@localhost')
    return bool(contact)


def _mldonkey_submit_command(browser, command):
    """Submit a command to mldonkey."""
    with browser.get_iframe('commands') as commands_frame:
        commands_frame.find_by_css('.txt2').fill(command)
        commands_frame.find_by_css('.but2').click()


def mldonkey_remove_all_ed2k_files(browser):
    """Remove all ed2k files from mldonkey."""
    browser.visit(config['DEFAULT']['url'] + '/mldonkey/')
    _mldonkey_submit_command(browser, 'cancel all')
    _mldonkey_submit_command(browser, 'confirm yes')


def mldonkey_upload_sample_ed2k_file(browser):
    """Upload a sample ed2k file into mldonkey."""
    browser.visit(config['DEFAULT']['url'] + '/mldonkey/')
    dllink_command = 'dllink ed2k://|file|foo.bar|123|0123456789ABCDEF0123456789ABCDEF|/'
    _mldonkey_submit_command(browser, dllink_command)


def mldonkey_get_number_of_ed2k_files(browser):
    """Return the number of ed2k files currently in mldonkey."""
    browser.visit(config['DEFAULT']['url'] + '/mldonkey/')

    with browser.get_iframe('commands') as commands_frame:
        commands_frame.find_by_xpath(
            '//tr//td[contains(text(), "Transfers")]').click()

    with browser.get_iframe('output') as output_frame:
        return len(output_frame.find_by_css('.dl-1')) + len(
            output_frame.find_by_css('.dl-2'))


def transmission_remove_all_torrents(browser):
    """Remove all torrents from transmission."""
    browser.visit(config['DEFAULT']['url'] + '/transmission')
    while True:
        torrents = browser.find_by_css('#torrent_list .torrent')
        if not torrents:
            break

        torrents.first.click()
        eventually(browser.is_element_not_present_by_css,
                   args=['#toolbar-remove.disabled'])
        browser.click_link_by_id('toolbar-remove')
        eventually(browser.is_element_not_present_by_css,
                   args=['#dialog-container[style="display: none;"]'])
        browser.click_link_by_id('dialog_confirm_button')
        eventually(browser.is_element_present_by_css,
                   args=['#toolbar-remove.disabled'])


def transmission_upload_sample_torrent(browser):
    """Upload a sample torrent into transmission."""
    browser.visit(config['DEFAULT']['url'] + '/transmission')
    file_path = os.path.join(os.path.dirname(__file__), '..', 'data',
                             'sample.torrent')
    browser.click_link_by_id('toolbar-open')
    eventually(browser.is_element_not_present_by_css,
               args=['#upload-container[style="display: none;"]'])
    browser.attach_file('torrent_files[]', [file_path])
    browser.click_link_by_id('upload_confirm_button')
    eventually(browser.is_element_present_by_css,
               args=['#torrent_list .torrent'])


def transmission_get_number_of_torrents(browser):
    """Return the number torrents currently in transmission."""
    browser.visit(config['DEFAULT']['url'] + '/transmission')
    return len(browser.find_by_css('#torrent_list .torrent'))


def _deluge_get_active_window_title(browser):
    """Return the title of the currently active window in Deluge."""
    return browser.evaluate_script(
        'Ext.WindowMgr.getActive() ? Ext.WindowMgr.getActive().title : null')


def _deluge_ensure_logged_in(browser):
    """Ensure that password dialog is answered and we can interact."""
    url = config['DEFAULT']['url'] + '/deluge'

    def service_is_available():
        if browser.is_element_present_by_xpath(
                '//h1[text()="Service Unavailable"]'):
            access_url(browser, 'deluge')
            return False

        return True

    if browser.url != url:
        browser.visit(url)
        # After a backup restore, service may not be available immediately
        eventually(service_is_available)

        time.sleep(1)  # Wait for Ext.js application in initialize

    if _deluge_get_active_window_title(browser) != 'Login':
        return

    browser.find_by_id('_password').first.fill('deluge')
    _deluge_click_active_window_button(browser, 'Login')

    assert eventually(
        lambda: _deluge_get_active_window_title(browser) != 'Login')
    eventually(browser.is_element_not_present_by_css,
               args=['#add.x-item-disabled'], timeout=0.3)


def _deluge_open_connection_manager(browser):
    """Open the connection manager dialog if not already open."""
    title = 'Connection Manager'
    if _deluge_get_active_window_title(browser) == title:
        return

    browser.find_by_css('button.x-deluge-connection-manager').first.click()
    eventually(lambda: _deluge_get_active_window_title(browser) == title)


def _deluge_ensure_connected(browser):
    """Type the connection password if required and start Deluge daemon."""
    _deluge_ensure_logged_in(browser)

    # Change Default Password window appears once.
    if _deluge_get_active_window_title(browser) == 'Change Default Password':
        _deluge_click_active_window_button(browser, 'No')

    assert eventually(browser.is_element_not_present_by_css,
                      args=['#add.x-item-disabled'])


def deluge_remove_all_torrents(browser):
    """Remove all torrents from deluge."""
    _deluge_ensure_connected(browser)

    while browser.find_by_css('#torrentGrid .torrent-name'):
        browser.find_by_css('#torrentGrid .torrent-name').first.click()

        # Click remove toolbar button
        browser.find_by_id('remove').first.click()

        # Remove window shows up
        assert eventually(lambda: _deluge_get_active_window_title(browser) ==
                          'Remove Torrent')

        _deluge_click_active_window_button(browser, 'Remove With Data')

        # Remove window disappears
        assert eventually(lambda: not _deluge_get_active_window_title(browser))


def _deluge_get_active_window_id(browser):
    """Return the ID of the currently active window."""
    return browser.evaluate_script('Ext.WindowMgr.getActive().id')


def _deluge_click_active_window_button(browser, button_text):
    """Click an action button in the active window."""
    browser.execute_script('''
        active_window = Ext.WindowMgr.getActive();
        active_window.buttons.forEach(function (button) {{
            if (button.text == "{button_text}")
                button.btnEl.dom.click()
        }})'''.format(button_text=button_text))


def deluge_upload_sample_torrent(browser):
    """Upload a sample torrent into deluge."""
    _deluge_ensure_connected(browser)

    number_of_torrents = _deluge_get_number_of_torrents(browser)

    # Click add toolbar button
    browser.find_by_id('add').first.click()

    # Add window appears
    eventually(
        lambda: _deluge_get_active_window_title(browser) == 'Add Torrents')

    file_path = os.path.join(os.path.dirname(__file__), '..', 'data',
                             'sample.torrent')

    if browser.find_by_id('fileUploadForm'):  # deluge-web 2.x
        browser.attach_file('file', file_path)
    else:  # deluge-web 1.x
        browser.find_by_css('button.x-deluge-add-file').first.click()

        # Add from file window appears
        eventually(lambda: _deluge_get_active_window_title(browser) ==
                   'Add from File')

        # Attach file
        browser.attach_file('file', file_path)

        # Click Add
        _deluge_click_active_window_button(browser, 'Add')

        eventually(
            lambda: _deluge_get_active_window_title(browser) == 'Add Torrents')

    # Click Add
    time.sleep(1)
    _deluge_click_active_window_button(browser, 'Add')

    eventually(
        lambda: _deluge_get_number_of_torrents(browser) > number_of_torrents)


def _deluge_get_number_of_torrents(browser):
    """Return the number torrents currently in deluge."""
    return len(browser.find_by_css('#torrentGrid .torrent-name'))


def deluge_get_number_of_torrents(browser):
    """Return the number torrents currently in deluge."""
    _deluge_ensure_connected(browser)

    return _deluge_get_number_of_torrents(browser)


def calendar_is_available(browser):
    """Return whether calendar is available at well-known URL."""
    conf = config['DEFAULT']
    url = conf['url'] + '/.well-known/caldav'
    logging.captureWarnings(True)
    request = requests.get(url, auth=(conf['username'], conf['password']),
                           verify=False)
    logging.captureWarnings(False)
    return request.status_code != 404


def addressbook_is_available(browser):
    """Return whether addressbook is available at well-known URL."""
    conf = config['DEFAULT']
    url = conf['url'] + '/.well-known/carddav'
    logging.captureWarnings(True)
    request = requests.get(url, auth=(conf['username'], conf['password']),
                           verify=False)
    logging.captureWarnings(False)
    return request.status_code != 404


def _syncthing_load_main_interface(browser):
    """Close the dialog boxes that many popup after visiting the URL."""
    access_url(browser, 'syncthing')

    def service_is_available():
        if browser.is_element_present_by_xpath(
                '//h1[text()="Service Unavailable"]'):
            access_url(browser, 'syncthing')
            return False

        return True

    # After a backup restore, service may not be available immediately
    eventually(service_is_available)

    # Wait for javascript loading process to complete
    browser.execute_script('''
        document.is_ui_online = false;
        var old_console_log = console.log;
        console.log = function(message) {
            old_console_log.apply(null, arguments);
            if (message == 'UIOnline') {
                document.is_ui_online = true;
                console.log = old_console_log;
            }
        };
    ''')
    eventually(lambda: browser.evaluate_script('document.is_ui_online'),
               timeout=5)

    # Dismiss the Usage Reporting consent dialog
    usage_reporting = browser.find_by_id('ur').first
    eventually(lambda: usage_reporting.visible, timeout=2)
    if usage_reporting.visible:
        yes_xpath = './/button[contains(@ng-click, "declineUR")]'
        usage_reporting.find_by_xpath(yes_xpath).first.click()
        eventually(lambda: not usage_reporting.visible)


def syncthing_folder_is_present(browser, folder_name):
    """Return whether a folder is present in Syncthing."""
    _syncthing_load_main_interface(browser)
    folder_names = browser.find_by_css('#folders .panel-title-text span')
    folder_names = [folder_name.text for folder_name in folder_names]
    return folder_name in folder_names


def syncthing_add_folder(browser, folder_name, folder_path):
    """Add a new folder to Synthing."""
    _syncthing_load_main_interface(browser)
    add_folder_xpath = '//button[contains(@ng-click, "addFolder")]'
    browser.find_by_xpath(add_folder_xpath).click()

    folder_dialog = browser.find_by_id('editFolder').first
    eventually(lambda: folder_dialog.visible)
    browser.find_by_id('folderLabel').fill(folder_name)
    browser.find_by_id('folderPath').fill(folder_path)
    save_folder_xpath = './/button[contains(@ng-click, "saveFolder")]'
    folder_dialog.find_by_xpath(save_folder_xpath).first.click()
    eventually(lambda: not folder_dialog.visible)


def syncthing_remove_folder(browser, folder_name):
    """Remove a folder from Synthing."""
    _syncthing_load_main_interface(browser)

    # Find folder
    folder = None
    for current_folder in browser.find_by_css('#folders > .panel'):
        name = current_folder.find_by_css('.panel-title-text span').first.text
        if name == folder_name:
            folder = current_folder
            break

    # Edit folder button
    folder.find_by_css('button.panel-heading').first.click()
    eventually(lambda: folder.find_by_css('div.collapse.in'))
    edit_folder_xpath = './/button[contains(@ng-click, "editFolder")]'
    edit_folder_button = folder.find_by_xpath(edit_folder_xpath).first
    edit_folder_button.click()

    # Edit folder dialog
    folder_dialog = browser.find_by_id('editFolder').first
    eventually(lambda: folder_dialog.visible)
    remove_button_xpath = './/button[contains(@data-target, "remove-folder")]'
    folder_dialog.find_by_xpath(remove_button_xpath).first.click()

    # Remove confirmation dialog
    remove_folder_dialog = browser.find_by_id('remove-folder-confirmation')
    eventually(lambda: remove_folder_dialog.visible)
    remove_button_xpath = './/button[contains(@ng-click, "deleteFolder")]'
    remove_folder_dialog.find_by_xpath(remove_button_xpath).first.click()

    eventually(lambda: not folder_dialog.visible)


def _ttrss_load_main_interface(browser):
    """Load the TT-RSS interface."""
    access_url(browser, 'tt-rss')
    overlay = browser.find_by_id('overlay')
    eventually(lambda: not overlay.visible)


def _ttrss_is_feed_shown(browser, invert=False):
    return browser.is_text_present('Planet Debian') != invert


def ttrss_subscribe(browser):
    """Subscribe to a feed in TT-RSS."""
    _ttrss_load_main_interface(browser)
    browser.find_by_text('Actions...').click()
    browser.find_by_text('Subscribe to feed...').click()
    browser.find_by_id('feedDlg_feedUrl').fill(
        'https://planet.debian.org/atom.xml')
    browser.find_by_text('Subscribe').click()
    if browser.is_text_present('You are already subscribed to this feed.'):
        browser.find_by_text('Cancel').click()

    expand = browser.find_by_css('span.dijitTreeExpandoClosed')
    if expand:
        expand.first.click()

    assert eventually(_ttrss_is_feed_shown, [browser])


def ttrss_unsubscribe(browser):
    """Unsubscribe from a feed in TT-RSS."""
    _ttrss_load_main_interface(browser)
    expand = browser.find_by_css('span.dijitTreeExpandoClosed')
    if expand:
        expand.first.click()

    browser.find_by_text('Planet Debian').click()
    browser.execute_script("quickMenuGo('qmcRemoveFeed')")
    prompt = browser.get_alert()
    prompt.accept()

    assert eventually(_ttrss_is_feed_shown, [browser, True])


def ttrss_is_subscribed(browser):
    """Return whether subscribed to a feed in TT-RSS."""
    _ttrss_load_main_interface(browser)
    return browser.is_text_present('Planet Debian')
