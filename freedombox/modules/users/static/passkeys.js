// SPDX-License-Identifier: AGPL-3.0-or-later
/**
 * @licstart The following is the entire license notice for the JavaScript
 * code in this page.
 *
 * This file is part of FreedomBox.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as
 * published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 * @licend The above is the entire license notice for the JavaScript code
 * in this page.
 */

/*
 * Decode a given base64 encoded (in web-mode) string to a binary array.
 */
function base64WebDecode(base64WebString) {
    let base64String = base64WebString
        .replaceAll('-', '+')
        .replaceAll('_', '/');
    const padding = base64String.length % 4;
    if (padding != 0) {
        base64String += '='.repeat(4 - padding);
    }

    const binaryString = atob(base64String);
    const binaryArray = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
        binaryArray[i] = binaryString.charCodeAt(i);
    }

    return binaryArray;
}

/*
 * Show an error as an bootstrap alert message and print to browser debug
 * console.
 */
function handleError(error_string, exception) {
    console.log(error_string, exception);
    const template = document.getElementById('passkey-message-template');
    template.querySelector('.message').innerText = exception.toString();
    const messages = document.getElementById('passkey-messages');
    messages.insertAdjacentHTML('beforeEnd', template.innerHTML);
}

/*
 * Make a window.fetch() request and handle some common errors.
 */
async function jsonFetch(relative_url, options, operation) {
    let response, json = null;
    const consoleError = 'Could not perform operation: ' + operation;
    try {
        const url = new URL(relative_url, window.location.href);
        response = await window.fetch(url, options);
        json = await response.json();
    } catch (error) {
        handleError(consoleError, error);
        return null;
    }

    if (response.ok && json) {
        return json;
    }

    if (json && json['error_string']) {
        handleError(consoleError, json['error_string']);
    } else {
        handleError(consoleError, `${response.status}: ${response.statusText}`);
    }

    return null;
}

/*
 * Add a passkey. First send a request to the server to begin passkey creation
 * and get challenge and creation options. Then request the browser to talk to
 * the authenticator to create a passkey. Finally, pass the public key of the
 * newly create passkey along with creation results to the server.
 */
async function addPasskey(csrfToken) {
    console.log('Adding passkey');

    if (!window.PublicKeyCredential) {
        const message = document.getElementById(
            'browser-does-not-support-passkeys').innerText.trim();
        handleError('Browser does not support passkeys', message);
        return;
    }

    //
    // Request challenge and options from server.
    //
    let options = await jsonFetch('add-begin/', {
            'method': 'POST',
            body: new URLSearchParams({'csrfmiddlewaretoken': csrfToken})
    }, 'initiate passkey registration');
    if (!options) {
        return;
    }

    options['publicKey']['user']['id'] = base64WebDecode(
        options['publicKey']['user']['id']);
    options['publicKey']['challenge'] = base64WebDecode(
        options['publicKey']['challenge']);

    //
    // Create new key pair on the authenticator (via the browser).
    //
    let credential;
    try {
        credential = await navigator.credentials.create(
            {'publicKey': options['publicKey']});
    } catch (error) {
        handleError('Passkey registration failed.', error);
        return;
    }

    //
    // Send the public key and authenticator response to the server for
    // verification and storage.
    //
    let completeResponse = await jsonFetch('add-complete/', {
            'method': 'POST',
            'headers': {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            'body': JSON.stringify(credential),
        }, 'passkey registration');
    if (!completeResponse) {
        return;
    }

    console.log('Passkey registration succeeded.');
    window.location.reload();
};

/*
 * Show a confirmation dialog to the user to delete a passkey.
 */
function onPasskeyDeleteClicked(event) {
    const modalElement = document.getElementById('passkey-delete-confirm-dialog');
    const modal = new bootstrap.Modal(modalElement);

    const passkeyElement = event.target.closest('.passkey');
    const nameElements = modalElement.querySelectorAll('.passkey-name');
    nameElements.forEach((element) => {
        element.innerText = passkeyElement.dataset.passkeyName;
    });
    modalElement.dataset.passkeyId = passkeyElement.dataset.passkeyId;

    event.preventDefault();
    modal.show();
}

/*
 * Send request to the server to delete a passkey by submitting a form (and
 * refreshing the page).
 */
function onPasskeyDeleteConfirmed(event) {
    const modelElement = document.getElementById('passkey-delete-confirm-dialog');
    const passkeyId = modelElement.dataset.passkeyId;
    const form = document.querySelector(
        `[data-passkey-id="${passkeyId}"] .form-passkey-delete`);
    form.submit();
}

/*
 * Attach event handler to 'Add Passkey', 'Delete Passkey', and 'Confirm Delete'
 * buttons. Retrieve CSRF token and pass it along.
 */
document.addEventListener('DOMContentLoaded', () => {
    const addPasskeyButton = document.getElementById('add-passkey');
    if (!addPasskeyButton) {
        // Not part of the Manage Passkeys page.
        return;
    }

    const csrfToken = document.getElementsByName('csrfmiddlewaretoken')[0].value;

    addPasskeyButton.addEventListener('click', async (event) => {
        event.preventDefault();
        await addPasskey(csrfToken);
    });

    const deleteButtons = document.querySelectorAll(
        '.passkey-delete-button');
    deleteButtons.forEach((element) => {
        element.addEventListener('click', onPasskeyDeleteClicked);
    });

    const confirmDeleteButton = document.querySelector(
        '#passkey-delete-confirm-dialog .confirm');
    confirmDeleteButton.addEventListener('click', onPasskeyDeleteConfirmed);
});


let passkeyLoginAbortController = null;

/*
 * Login with a passkey. First send a request to the server to begin logging in
 * with passkey and get challenge and login operation options. Then request the
 * browser to talk to the authenticator to sign the challenge with a passkey.
 * Finally, pass the challenge signed with a known passkey along with other
 * results to the server.
 */
async function loginWithPasskey(conditionalMediation, csrfToken, next) {
    console.log('Signing in with a passkey. Conditional mediation: ',
                conditionalMediation);

    if (!window.PublicKeyCredential) {
        if (!conditionalMediation) {
            const message = document.getElementById(
                'browser-does-not-support-passkeys').innerText.trim();
            handleError('Browser does not support passkeys', message);
        }
        return;
    }

    //
    // Request challenge and options from server.
    //
    const options = await jsonFetch('passkey-begin/', {
            'method': 'POST',
            body: new URLSearchParams({'csrfmiddlewaretoken': csrfToken})
    }, 'initiate passkey login');
    if (!options) {
        return;
    }

    options['publicKey']['challenge'] = base64WebDecode(
        options['publicKey']['challenge']);

    // Abort a previous login operation (such as conditional mediation operation
    // if it is running). Firefox automatically does this but Chrome does not.
    if (passkeyLoginAbortController) {
        console.log('Explicitly aborting previous passkey login operation.');
        passkeyLoginAbortController.abort();
    }

    passkeyLoginAbortController = new AbortController();

    //
    // Sign the server challenge with passkey stored in authenticator (via the
    // browser).
    //
    let credential;
    try {
        const getOptions = {
            'publicKey': options['publicKey'],
            'signal': passkeyLoginAbortController.signal
        };
        if (conditionalMediation) {
            getOptions['mediation'] = 'conditional';
        }
        credential = await navigator.credentials.get(getOptions);
    } catch (error) {
        if (conditionalMediation && error.name == 'AbortError') {
            // When user clicks on 'Log in with passkey', the process initiated
            // with conditional mediation will be aborted.
            console.log('Log in initiated with button, ' +
                        'conditional mediation aborted.');
            return;
        }
        if (!conditionalMediation) {
            // Don't show error message or retry.
            handleError('Login with passkey failed.', error);
        }
        return;
    }

    // Send the signature and the authenticator response to the server to
    // complete the login process.
    let completeResponse = await jsonFetch('passkey-complete/', {
            'method': 'POST',
            'headers': {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            'body': JSON.stringify(credential),
    }, 'login with passkey');
    if (!completeResponse) {
        return;
    }

    console.log('Login with passkey succeeded.');
    window.location.href = next;
}

/*
 * Attach an click event listener to 'Log in with passkey' button.
 */
document.addEventListener('DOMContentLoaded', async () => {
    const loginWithPasskeyButton = document.getElementById('login-with-passkey');
    if (!loginWithPasskeyButton) {
        // Not part of login page.
        return;
    }

    const csrfToken = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    const next = document.getElementsByName('next')[0].value;
    loginWithPasskeyButton.addEventListener('click', async (event) => {
        event.preventDefault();
        await loginWithPasskey(false, csrfToken, next);
    });

    // Login with conditional mediation. This means that user will see a
    // 'passkey' option with autofill in the username field. The login method
    // will be wait in the navigator.credentials.get() call until user selects
    // that option. Don't await.
    loginWithPasskey(true, csrfToken, next);
});
