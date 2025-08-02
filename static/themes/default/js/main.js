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
 * Remove the 'no-js' class from the <body> element. CSS utilizing this can
 * create different rules when Javascript is available and when it is not. This
 * functionality was provided by the Modernizr library earlier.
 */
document.addEventListener('DOMContentLoaded', function (event) {
    const html = document.querySelector('html');
    html.classList.remove('no-js');
    html.classList.add('js');
});

/*
 * Refresh page if marked for refresh.
 */
document.addEventListener('DOMContentLoaded', function () {
    const body = document.querySelector('body');
    if (body.hasAttribute('data-refresh-page-sec')) {
        let seconds = body.getAttribute('data-refresh-page-sec');
        seconds = parseInt(seconds, 10);
        if (isNaN(seconds))
            return;

        window.setTimeout(() => {
            // Refresh the page without resubmitting the POST data.
            window.location = window.location.href;
        }, seconds * 1000);
    }
});

/*
 * Return all submit buttons on the page
 */
function getSubmitButtons() {
    return document.querySelectorAll(
        "form input[type='submit'], form button[type='submit'].toggle-button");
}

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
        button.classList.contains('pull-right') ||
        button.hasAttribute('disabled')) {
        return;
    }

    // Don't disable the submit button immediately as that will prevent the
    // button from being sent in the HTTP request. Instead schedule disabling
    // for the next event loop run which will happen after current event is
    // processed.
    window.setTimeout(() => {
        if (button.tagName == "INPUT") {
            // For push buttons
            const beforeElement = document.createElement('div');
            beforeElement.classList.add('running-status-button-before');
            button.parentNode.insertBefore(beforeElement, button);
        } else if (button.tagName == "BUTTON") {
            // For toggle buttons
            button.classList.toggle('toggle-button--toggled');
        }

        button.classList.add('running-status-button');

        // Disable all form submit buttons on the page
        for (const formbutton of getSubmitButtons()) {
            if (!(formbutton.classList.contains('btn-link') ||
                formbutton.classList.contains('no-running-status') ||
                formbutton.hasAttribute('disabled'))) {
                formbutton.classList.add('temporarily-disabled');
                formbutton.setAttribute('disabled', 'disabled');
            }
        }
    }, 0);
}

document.addEventListener('DOMContentLoaded', function (event) {
    for (const button of getSubmitButtons()) {
        // Don't listen for 'click' event on buttons as they are triggered
        // even when the form is invalid.
        button.form.addEventListener('submit', onSubmitAddProgress);
    }
});

/*
 * Clear button disabling on the page.
 */
function clearButtonDisabling(event) {
    for (const button of getSubmitButtons()) {
        button.classList.remove('running-status-button');
        if (button.classList.contains('temporarily-disabled')) {
            button.classList.remove('temporarily-disabled');
            button.removeAttribute('disabled');
        }
    }

    const beforeSelector = ".running-status-button-before";
    const beforeElements = document.querySelectorAll(beforeSelector);
    for (const element of beforeElements) {
        element.remove();
    }
};

// When using back/forward browser's bfcache is used and pages won't receive
// 'load' events. Instead a 'pageshow' event is available. When a user does
// back/forward we want them to be able to submit the forms again. So clear all
// the button disabling.
window.addEventListener('pageshow', clearButtonDisabling);

/*
 * Select all option for multiple checkboxes.
 */
document.addEventListener('DOMContentLoaded', function (event) {
    // Django < 4.0 generates <ul> and <li> where as Django >= 4.0 generates <div>s
    let parents = document.querySelectorAll('ul.has-select-all,div.has-select-all');
    for (const parent of parents) {
        let childElementType = 'div';
        if (parent.tagName.toLowerCase() == 'ul')
            childElementType = 'li';

        let selectAllItem = document.createElement(childElementType);

        let label = document.createElement('label');
        label.for = "select_all";
        label.setAttribute('class', 'select-all-label');

        let checkbox = document.createElement('input');
        checkbox.type = "checkbox";
        checkbox.setAttribute('class', 'select-all');

        label.appendChild(checkbox);
        selectAllItem.appendChild(label);

        parent.insertBefore(selectAllItem, parent.childNodes[0]);
        setSelectAllValue(parent);

        checkbox.addEventListener('change', onSelectAllChanged);

        options = parent.querySelectorAll('input.has-select-all');
        for (const option of options) {
            option.addEventListener('change', onSelectAllOptionsChanged);
        }
    }
});

// When there is a change on the "select all" checkbox, set the checked property
// of all the checkboxes to the value of the "select all" checkbox
function onSelectAllChanged(event) {
    const selectAllCheckbox = event.currentTarget;
    const parent = selectAllCheckbox.parentElement.parentElement.parentElement;
    const options = parent.querySelectorAll('input.has-select-all');
    for (const option of options) {
        option.checked = selectAllCheckbox.checked;
    }
}

// When there is a change on a checkbox controlled by a select all checkbox,
// update the value of checkbox.
function onSelectAllOptionsChanged(event) {
    const parent = event.currentTarget.parentElement.parentElement.parentElement;
    setSelectAllValue(parent);
}

// Set/reset the checked property of "select all" checkbox based on whether all
// checkboxes it controls are checked.
function setSelectAllValue(parent) {
    const options = parent.querySelectorAll('input.has-select-all');
    let enableSelectAll = true;
    for (const option of options) {
        if (!option.checked) {
            enableSelectAll = false;
            break;
        }
    }

    parent.querySelector('.select-all').checked = enableSelectAll;
}

/*
 * Check whether an app is available on its setup page.
 */
document.addEventListener('DOMContentLoaded', async () => {
    const checkingElement = document.querySelector('.app-checking-availability');
    if (!checkingElement)
        return;

    // App does not need setup, it likely needs upgrade
    const setupState = checkingElement.getAttribute('data-setup-state');
    if (setupState !== 'needs-setup')
        return;

    const appId = checkingElement.getAttribute('data-app-id');
    checkingElement.classList.remove('d-none');

    function setInstallButtonState(enable) {
        const installButton = document.querySelector('.install-button');
        if (enable)
            installButton?.removeAttribute('disabled')
        else
            installButton?.setAttribute('disabled', 'disabled');
    }

    function error() {
        const element = document.querySelector('.app-checking-availability-error');
        element.classList.remove('d-none');
        checkingElement.classList.add('d-none');
        setInstallButtonState(true); // Allow trying installation
    }

    try {
        setInstallButtonState(false);
        const response = await fetch(`/plinth/is-available/${appId}/`, {
            timeout: 2 * 60 * 1000  // 2 minutes
        });

        checkingElement.classList.add('d-none');

        if (response.ok) {
            const data = await response.json();
            if (data.is_available === true) {
                setInstallButtonState(true);
            } else if (data.is_available === false) {
                document.querySelector('.app-unavailable').classList.remove('d-none');
                setInstallButtonState(false);
            } else {
                error();
            }
        } else {
            error();
        }
    } catch {
        error();
    }
});
