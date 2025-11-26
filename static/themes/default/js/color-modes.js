// SPDX-License-Identifier: CC-BY-3.0
/*
  This file is part of FreedomBox. Color mode toggler for Bootstrap's docs
  (https://getbootstrap.com/). Copyright 2011-2025 The Bootstrap Authors.

  @licstart  The following is the entire license notice for the
  JavaScript code in this page.

  Licensed under the Creative Commons Attribution 3.0 Unported License.

  @licend  The above is the entire license notice
  for the JavaScript code in this page.
*/

(() => {
    'use strict';

    const getStoredTheme = () => localStorage.getItem('theme');
    const setStoredTheme = theme => localStorage.setItem('theme', theme);

    const getBrowserTheme = () => {
        return window.matchMedia('(prefers-color-scheme: dark)')
            .matches ? 'dark' : 'light';
    };

    const getPreferredTheme = () => {
        const storedTheme = getStoredTheme();
        if (storedTheme) {
            return storedTheme;
        }

        return getBrowserTheme();
    };

    const setTheme = (theme) => {
        if (theme === 'auto') {
            theme = getBrowserTheme();
        }
        document.documentElement.setAttribute('data-bs-theme', theme);
    };

    setTheme(getPreferredTheme());

    const showActiveTheme = (theme, focus = false) => {
        const themeSwitcher = document.querySelector('#id_theme_menu_link');

        if (!themeSwitcher) {
            return;
        }

        const themeSwitcherText = document.querySelector('#id_toggle_theme_text');
        const activeThemeIcon = document.querySelector('#id_active_theme_icon');
        const btnToActive = document.querySelector(`[data-bs-theme-value="${theme}"]`);
        const iconOfActiveBtn = btnToActive.dataset.bsIconValue;

        document.querySelectorAll('[data-bs-theme-value]').forEach(element => {
            element.classList.remove('active');
            element.setAttribute('aria-pressed', 'false');
            const iconOfBtn = element.dataset.bsIconValue;
            if (activeThemeIcon.classList.contains(iconOfBtn)) {
                activeThemeIcon.classList.remove(iconOfBtn);
            }
        });

        btnToActive.classList.add('active');
        btnToActive.setAttribute('aria-pressed', 'true');
        activeThemeIcon.classList.add(iconOfActiveBtn);
        const themeSwitcherLabel = `${themeSwitcherText.textContent} (${btnToActive.dataset.bsThemeValue})`;
        themeSwitcher.setAttribute('title', themeSwitcherLabel);

        if (focus) {
            themeSwitcher.focus();
        };
    };

    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
        const storedTheme = getStoredTheme();
        if (storedTheme !== 'light' && storedTheme !== 'dark') {
            setTheme(getPreferredTheme());
        }
    });

    window.addEventListener('DOMContentLoaded', () => {
        showActiveTheme(getPreferredTheme());

        document.querySelectorAll('[data-bs-theme-value]')
            .forEach(toggle => {
                toggle.addEventListener('click', () => {
                    const theme = toggle.getAttribute('data-bs-theme-value');
                    setStoredTheme(theme);
                    setTheme(theme);
                    showActiveTheme(theme, true);
                });
            });
    });
})();
