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

/**
 * Update the URL path and history based on the selected tags.
 *
 * If no tags are selected, redirects to the base apps path. Otherwise,
 * constructs a new URL with query parameters for each tag and updates
 * the browser history.
 *
 * @param {string[]} tags - An array of selected tag names.
 */
function updatePath(tags) {
    const appsPath = window.location.pathname;
    if (tags.length === 0) {
        this.location.assign(appsPath);
    } else {
        let queryParams = tags.map(tag => `tag=${tag}`).join('&');
        let newPath = `${appsPath}?${queryParams}`;
        this.history.pushState({ tags: tags }, '', newPath);
        this.location.assign(newPath);
    }
}

/**
 * Get a list of tags currently displayed, excluding a specific tag if provided.
 *
 * Iterates through the tag badges in the UI, extracts their text content,
 * and returns an array of tag names.
 *
 * @param {string} [tagToRemove] - The name of the tag to exclude.
 * @returns {string[]} An array of tag names currently displayed.
 */
function getTags(tagToRemove) {
    const tagBadges = document.querySelectorAll('#selected-tags .tag-badge');
    return Array.from(tagBadges)
        .map(tag => tag.dataset.tag)
        .filter(tagName => tagName !== tagToRemove);
}

/**
 * Filter and highlight the best matching tag based on the search term.
 *
 * This function updates the visibility and highlighting of dropdown items
 * to match the user's input in the search box. It determines the best
 * matching item and marks it as active.
 *
 * @param {KeyboardEvent} event - The keyboard event that triggered the search.
 */
function findMatchingTag(addTagInput, dropdownItems) {
    const searchTerm = addTagInput.value.toLowerCase().trim();

    // Remove highlighting from all items
    dropdownItems.forEach(item => item.classList.remove('active'));

    let bestMatch = null;
    dropdownItems.forEach(item => {
        const text = item.textContent.toLowerCase();
        if (text.includes(searchTerm)) {
            item.style.display = 'block';
            function matchesEarly () {
                return text.indexOf(searchTerm) < bestMatch.textContent.toLowerCase().indexOf(searchTerm);
            };
            if (bestMatch === null || matchesEarly()) {
                bestMatch = item;
            }
        } else {
            item.style.display = 'none';
        }
    });

    // Highlight the best match
    if (bestMatch) {
        bestMatch.classList.add('active');
    }
}

/**
 * Manage tag-related UI interactions for filtering and displaying apps.
 *
 * This script manages the user interface for filtering apps based on
 * selected tags. It provides functionality for adding and removing tags,
 * updating the URL based on selected tags, and displaying a set of
 * available tags in a searchable dropdown.
 */
document.addEventListener('DOMContentLoaded', function () {

    // Remove Tag handler.
    document.querySelectorAll('.remove-tag').forEach(button => {
        button.addEventListener('click', () => {
            let tag = button.parentElement.dataset.tag;
            let tags = getTags(tag);
            updatePath(tags);
        });
    });

    /**
     * Searchable dropdown for selecting tags.
     *
     * As the user types in the input field, the dropdown list is filtered
     * to show only matching items. The best matching item (first match if
     * multiple match) is highlighted. Pressing Enter selects the
     * highlighted item and adds it as a tag.
     */
    const addTagInput = document.getElementById('add-tag-input');
    const dropdownItems = document.querySelectorAll('li.dropdown-item');

    var timeoutId;
    addTagInput.addEventListener('keyup', (event) => {
        clearTimeout(timeoutId);
        // Select the active tag if the user pressed Enter
        if (event.key === 'Enter') {
            dropdownItems.forEach(item => {
                if (item.classList.contains('active')) {
                    item.click();
                }
            });
        }
        // Debounce the user input for search with 300ms delay.
        timeoutId = setTimeout(findMatchingTag(addTagInput, dropdownItems), 300);
    });

    dropdownItems.forEach(item => {
        item.addEventListener('click', () => {
            const selectedTag = item.dataset.value;

            // Add the selected tag and update the path.
            let tags = getTags('');
            tags.push(selectedTag);
            updatePath(tags);

            // Reset the input field and dropdown.
            addTagInput.value = '';
            dropdownItems.forEach(item => {
                item.style.display = '';
                item.classList.remove('active');
            });
        });
    });

    // Handle browser back/forward navigation.
    window.addEventListener('popstate', function (event) {
        if (event.state && event.state.tags) {
            updatePath(event.state.tags);
        }
    });
});

