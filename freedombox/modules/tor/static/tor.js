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

document.addEventListener('DOMContentLoaded', () => {
    const relayEnabled = document.getElementById('id_tor-relay_enabled');
    const bridgeRelay = document.getElementById('id_tor-bridge_relay_enabled');
    const useUpstreamBridges = document.getElementById('id_tor-use_upstream_bridges');
    const upstreamBridgesField = document.getElementById('id_tor-upstream_bridges')
          .closest('.form-group');

    function handleRelayChange() {
        const disable = !relayEnabled.checked;
        bridgeRelay.disabled = disable;
        if (disable) {
            bridgeRelay.checked = false;
        }
    }

    function handleUseUpstreamBridgesChange() {
        if (useUpstreamBridges.checked) {
            upstreamBridgesField.style.display = '';
            relayEnabled.checked = false;
            relayEnabled.disabled = true;
            bridgeRelay.checked = false;
            bridgeRelay.disabled = true;
        } else {
            upstreamBridgesField.style.display = 'none';
            relayEnabled.disabled = false;
        }
    }

    relayEnabled.addEventListener('change', handleRelayChange);
    useUpstreamBridges.addEventListener('change', handleUseUpstreamBridgesChange);

    // Initial state
    handleRelayChange();
    handleUseUpstreamBridgesChange();
});
