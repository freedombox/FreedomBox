# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for RSS-Bridge app.
"""

import json
import subprocess

from plinth.tests import functional


class TestRSSBridgeApp(functional.BaseAppTests):
    app_name = 'rssbridge'
    has_service = False
    has_web = True

    def test_active_bridges(self, session_browser):
        """Check that bridges are active."""
        functional.app_enable(session_browser, self.app_name)
        functional.visit(session_browser, '/rss-bridge/')
        assert session_browser.find_by_css(
            '#bridge-Wikipedia button[type="submit"]')

    def test_feed_html(self, session_browser):
        """Check that a feed is properly rendered."""
        functional.app_enable(session_browser, self.app_name)
        url = '/rss-bridge/?action=display&bridge=Wikipedia&' \
            'language=en&subject=tfa&format=Html'
        functional.visit(session_browser, url)
        assert not session_browser.find_by_css('.exception-message')
        assert session_browser.find_by_css('.feeditem')

    def test_feed_json(self, session_browser):
        """Check that a feed is properly rendered."""
        functional.app_enable(session_browser, self.app_name)
        path = '/rss-bridge/?action=display&bridge=Wikipedia&' \
            'language=en&subject=tfa&format=Json'
        url = functional.config['DEFAULT']['url'] + path

        # Unauthorized
        result = subprocess.run(['curl', '-k', '--basic', url],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, check=True)
        assert '401 Unauthorized' in result.stdout.decode()

        # Authorized
        username = functional.config['DEFAULT']['username']
        password = functional.config['DEFAULT']['password']
        result = subprocess.run(
            ['curl', '-k', '--basic', '--user', f'{username}:{password}', url],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True)
        feed = json.loads(result.stdout)
        assert len(feed['items'])
