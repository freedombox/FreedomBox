/*
#
# This file is part of Plinth.
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

# This file based on example code from Javascript XMPP Client which is
# licensed as follows.
#
# The MIT License (MIT)
#
# Copyright (c) 2014 Klaus Herberth <klaus@jsxc.org>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
*/

$(function() {
    var settings = {
        url: '/http-bind/',
        domain: plinth_settings.domainname
    };

    jsxc.init({
        loginForm: {
            form: '#jsxc-login-form',
            jid: '#jsxc-username',
            pass: '#jsxc-password',
            onAuthFail: 'ask',
        },
        checkFlash: false,
        rosterAppend: 'body',
        root: plinth_settings.jsxc_root,
        otr: {
            debug: true,
            SEND_WHITESPACE_TAG: true,
            WHITESPACE_START_AKE: true
        },
        loadSettings: function(username, password) {
            return {
                xmpp: {
                    url: settings.url,
                    domain: settings.domain,
                    resource: 'jsxc',
                    overwrite: true,
                    onlogin: true
                }
            };
        }
    });

    // Form elements which needs to be enabled/disabled
    var formElements = $('#jsxc-login-form').find('input');

    // Click on logout button to logout
    $('.logout').on('click', function() {
        jsxc.triggeredFromElement = true;
        return jsxc.xmpp.logout();
    });

    var logged_in_state = function() {
        formElements.prop('disabled', true);
        $('.submit').hide();
        $('.logout').show();
    }
    var logged_out_state = function() {
        formElements.prop('disabled', false);
        $('.submit').show();
        $('.logout').hide();
    }

    $(document).on('close.dialog.jsxc', function() {
        jsxc.debug('Event triggered close.dialog.jsxc');
    });

    $(document).on('connecting.jsxc', function() {
        jsxc.debug('Event triggered connecting.jsxc');
        formElements.prop('disabled', true);
    });

    $(document).on('restoreCompleted.jsxc', function() {
        jsxc.debug('Event triggered restoreCompleted.jsxc');
        logged_in_state();
    });

    $(document).on('connected.jsxc', function() {
        jsxc.debug('Event triggered connected.jsxc');
        logged_in_state();
    });

    $(document).on('authfail.jsxc', function() {
        jsxc.debug('Event triggered authfail.jsxc');
        logged_out_state();
        $('#jsxc-login-form').find('.submit').button('reset');
    });

    $(document).on('attached.jsxc', function() {
        jsxc.debug('Event triggered attached.jsxc');
        logged_in_state();
    });

    $(document).on('disconnected.jsxc', function() {
        $('#jsxc-login-form').find('button').button('reset');
        logged_out_state();
    });

    // Load xmpp domain from storage
    if (typeof localStorage.getItem('xmpp-domain') === 'string') {
        $('#xmpp-domain').val(localStorage.getItem('xmpp-domain'));
    } else {
        $('#xmpp-domain').val(settings.domain);
    }

    // Check bosh url, if input changed
    $('#xmpp-domain').on('input', function(){
        var self = $(this);

        var timeout = self.data('timeout');
        if (timeout) {
            clearTimeout(timeout);
        }

        var domain = $('#xmpp-domain').val();
        if (!domain) {
            // we need domain to test BOSH server
            return;
        }

        localStorage.setItem('xmpp-domain', domain);
        settings.domain = domain;

        $('#server-flash').removeClass('success fail').text('Testing...');

        // test only every 2 seconds
        timeout = setTimeout(function() {
            testBoshServer(settings.url, $('#xmpp-domain').val(), function(result) {
                $('#server-flash').removeClass('success fail').addClass(result.status).html(result.msg);
            });
        }, 2000);

        self.data('timeout', timeout);
    });

    // check initial bosh url
    $('#xmpp-domain').trigger('input');
});

/**
* Test if bosh server is up and running.
*
* @param  {string}   url    BOSH url
* @param  {string}   domain host domain for BOSH server
* @param  {Function} cb     called if test is done
*/
function testBoshServer(url, domain, cb) {
    var rid = jsxc.storage.getItem('rid') || '123456';

    function fail(m) {
        var msg = 'BOSH server NOT reachable or misconfigured.';

        if (typeof m === 'string') {
            msg += '<br /><br />' + m;
        }

        cb({
            status: 'fail',
            msg: msg
        });
    }

    $.ajax({
        type: 'POST',
        url: url,
        data: "<body rid='" + rid + "' xmlns='http://jabber.org/protocol/httpbind' to='" + domain + "' xml:lang='en' wait='60' hold='1' content='text/xml; charset=utf-8' ver='1.6' xmpp:version='1.0' xmlns:xmpp='urn:xmpp:xbosh'/>",
        global: false,
        dataType: 'xml'
    }).done(function(stanza) {
        if (typeof stanza === 'string') {
            // shouldn't be needed anymore, because of dataType
            stanza = $.parseXML(stanza);
        }

        var body = $(stanza).find('body[xmlns="http://jabber.org/protocol/httpbind"]');
        var condition = (body) ? body.attr('condition') : null;
        var type = (body) ? body.attr('type') : null;

        // we got a valid xml response, but we have test for errors

        if (body.length > 0 && type !== 'terminate') {
            cb({
                status: 'success',
                msg: 'BOSH Server reachable.'
            });
        } else {
            if (condition === 'internal-server-error') {
                fail('Internal server error: ' + body.text());
            } else if (condition === 'host-unknown') {
                if (url) {
                    fail('Host unknown: ' + domain + ' is unknown to your XMPP server.');
                } else {
                    fail('Host unknown: Please provide a XMPP domain.');
                }
            } else {
                fail(condition);
            }
        }
    }).fail(function(xhr, textStatus) {
        // no valid xml, not found or csp issue

        var fullurl;
        if (url.match(/^https?:\/\//)) {
            fullurl = url;
        } else {
            fullurl = window.location.protocol + '//' + window.location.host;
            if (url.match(/^\//)) {
                fullurl += url;
            } else {
                fullurl += window.location.pathname.replace(/[^/]+$/, "") + url;
            }
        }

        if(xhr.status === 0) {
            // cross-side
            fail('Cross domain request was not possible.');
        } else if (xhr.status === 404) {
            // not found
            fail('Your server responded with "404 Not Found". Please check if your BOSH server is running and reachable via ' + fullurl + '.');
        } else if (textStatus === 'parsererror') {
            fail('Invalid XML received. Maybe ' + fullurl + ' was redirected. You should use an absolute url.');
        } else {
            fail(xhr.status + ' ' + xhr.statusText);
        }
    });
}
