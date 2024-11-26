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
 * Update the URL path based on the selected tags.
 *
 * If no tags are selected, redirects to the base apps path. Otherwise,
 * constructs a new URL with query parameters for each tag.
 *
 * @param {string[]} tags - An array of selected tag names.
 */
function updatePathWithTags(tags) {
    const appsPath = window.location.pathname;
    if (tags.length === 0) {
        this.location.assign(appsPath);
    } else {
        const urlParams = new URLSearchParams();
        tags.forEach(tag => urlParams.append('tag', tag));
        this.location.search = urlParams;
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
        .map(tagBadge => tagBadge.dataset.tag)
        .filter(tag => tag !== tagToRemove);
}

/**
 * Filter and highlight the best matching tag based on the search term.
 *
 * This function updates the visibility and highlighting of dropdown items
 * to match the user's input in the search box. It determines the best
 * matching item and marks it as active.
 *
 * @param {ElementList} [dropdownItems] - List of items in the tags dropdown.
 */
function findMatchingTag(dropdownItems) {
    const addTagInput = document.getElementById('add-tag-input');
    const searchTerm = addTagInput.value.toLowerCase().trim();

    // Remove highlighting from all items
    dropdownItems.forEach(item => item.classList.remove('active'));

    let bestMatch = null;
    dropdownItems.forEach(item => {
        const text = item.dataset.tag_l10n.toLowerCase();
        if (text.includes(searchTerm)) {
            item.style.display = 'block';
            function matchesEarly () {
                let bestMatchText = bestMatch.dataset.tag_l10n.toLowerCase();
                return text.indexOf(searchTerm) < bestMatchText.indexOf(searchTerm);
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
 * Handle a key press event on that tag input field.
 *
 * As the user types in the input field, the dropdown list is filtered
 * to show only matching items. The best matching item (first match if
 * multiple match) is highlighted. Pressing Enter selects the
 * highlighted item and adds it as a tag.
 *
 * @param {KeyboardEvent} [event] - The key press event.
 */
function onTagInputKeyUp(event) {
    const dropdownItems = document.querySelectorAll('.tag-input li.dropdown-item');

    // Select the active tag if the user pressed Enter
    if (event.key === 'Enter') {
        dropdownItems.forEach(item => {
            if (item.classList.contains('active')) {
                item.click();
            }
        });
    }
    findMatchingTag(dropdownItems);
}

/**
 * When an item in the tags dropdown is clicked, navigate to a new URL with the
 * added Tag.
 *
 * @param {PointerEvent} [event] - The click event.
 */
function onTagInputDropdownItemClicked(event) {
    const item = event.currentTarget;
    const selectedTag = item.dataset.tag;

    // Add the selected tag and update the path.
    let tags = getTags('');
    tags.push(selectedTag);
    updatePathWithTags(tags);

    // Reset the input field
    const addTagInput = document.getElementById('add-tag-input');
    addTagInput.value = '';

    // Reset the dropdown
    const dropdownItems = document.querySelectorAll('.tag-input li.dropdown-item');
    dropdownItems.forEach(item => {
        item.style.display = 'none';
        item.classList.remove('active');
    });
}

/**
 * when an remove button next to a tag is clicked, navigate to a new URL without
 * that Tag.
 *
 * @param {PointerEvent} [event] - The click event.
 */
function onRemoveTagClicked(event) {
    const button = event.currentTarget;
    const tag = button.parentElement.dataset.tag;
    const tags = getTags(tag);
    updatePathWithTags(tags);
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
    document.querySelectorAll('.remove-tag').forEach(button => {
        button.addEventListener('click', onRemoveTagClicked);
    });

    const addTagInput = document.getElementById('add-tag-input');
    if (addTagInput) {  // When page loads without tag input element
        addTagInput.addEventListener('keyup', onTagInputKeyUp);
    }

    const dropdownItems = document.querySelectorAll('.tag-input li.dropdown-item');
    dropdownItems.forEach(item => {
        item.addEventListener('click', onTagInputDropdownItemClicked);
    });
});

