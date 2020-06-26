// SPDX-License-Identifier: AGPL-3.0-or-later
/*
  This file is part of FreedomBox.

  @licstart  The following is the entire license notice for the
  JavaScript code in this page.

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU Affero General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU Affero General Public License for more details.

  You should have received a copy of the GNU Affero General Public License
  along with this program.  If not, see <http://www.gnu.org/licenses/>.

  @licend  The above is the entire license notice
  for the JavaScript code in this page.
*/

/*
 * Disable submit button on click.
 */
function onSubmitAddProgress(event) {
    // Using activeElement is not reliable. If the user presses Enter on a text
    // field, activeElement with be that text field. However, we do safety
    // checks and fallback to not disabling/animating the submit button, which
    // is okay.
    button = document.activeElement;
    if (!button.classList.contains('btn') ||
        button.classList.contains('btn-link') ||
        button.classList.contains('no-running-status') ||
        button.hasAttribute('disabled')) {
        return;
    }

    // Don't disable the submit button immediately as that will prevent the
    // button from being sent in the HTTP request. Instead schedule disabling
    // for the next event loop run which will happen after current event is
    // processed.
    window.setTimeout(() => {
        const beforeElement = document.createElement('div');
        beforeElement.classList.add('running-status-button-before');
        button.parentNode.insertBefore(beforeElement, button);

        button.classList.add('running-status-button');
        button.setAttribute('disabled', 'disabled');
    }, 0);
}

document.addEventListener('DOMContentLoaded', function(event) {
    const submitButtons = document.querySelectorAll("input[type='submit']");
    for (const button of submitButtons) {
        if (button.form) {
            // Don't listen for 'click' event on buttons as they are triggered
            // even when the form is invalid.
            button.form.addEventListener('submit', onSubmitAddProgress);
        }
    }
});

// When using back/forward browser's bfcache is used and pages won't receive
// 'load' events. Instead a 'pageshow' event is available. When a user does
// back/forward we want them to be able to submit the forms again. So clear all
// the button disabling.
window.addEventListener('pageshow', function(event) {
    const selector = "input[type='submit'].running-status-button";
    const submitButtons = document.querySelectorAll(selector);
    for (const button of submitButtons) {
        button.classList.remove('running-status-button');
        button.removeAttribute('disabled');
    }

    const beforeSelector = ".running-status-button-before";
    const beforeElements = document.querySelectorAll(beforeSelector);
    for (const element of beforeElements) {
        element.remove();
    }
});
