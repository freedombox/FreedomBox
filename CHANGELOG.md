# Change Log
All notable changes to this project will be documented in this file.

## [0.14.0] - 2017-04-09
### Added
- tor: Added option to use upstream bridges.
- openvpn: Added to front page.
- openvpn: Non-admin users can download their own profiles.
- Added Debian badges to README.
- Added new locales for Hindi (hi) and Gujarati (gu).
- Added syncthing module for file synchronization.
- Added Matrix Synapse as chat server with groups, audio and video.

### Removed
- Removed use of stronghold whitelisting, no longer necessary.
- Removed unused symlink to doc directory.

### Changed
- Require admin access for all system configuration pages.
- Change appearance of topbar and footer.
- Use common LDAP auth apache configuration in all modules.

### Fixed
- Added missing shaarli logo.
- Overwrite existing doc and static folders when installing.
- Added line break to infinoted title, used by front page shortcut.
- Fixed URL in INSTALL doc.
- openvpn: Regenerate user key or certificate if empty.
- openvpn: Prevent failures when regenerating user certificate.
- Fixed augeas error in travis build.
- disks: Workaround issue in parted during resize.

## [0.13.1] - 2017-01-22
### Added
- Added new locale for Japanese (ja).

### Fixed
- setup: Fixed an infinite redirect in a rare case.
- Fixed URLs referencing jsxc JS and CSS files.
- setup.py: Install all first-run scripts for freedombox-setup.
- ikiwiki: Fixed showing icon for newly created wiki/blog.

## [0.13.0] - 2017-01-18
### Added
- Added command line argument --list-modules which will list modules
  and exit. It can be followed by "essential" or "optional" to only
  list those modules.
- Added JS license web labels for LibreJS.
- Added basic configuration form for Minetest server.
- Added Domain Name Server (BIND) module.
- help: Added indicator for new plinth version available.
- Added Gobby Server (infinoted) module.

### Changed
- frontpage: Show app logos instead of generic icons.
- Prevent anonymous users from accessing setup pages.
- Firstboot, KVStore: merge old firstboot state fields.
- tor: Use Plinth-specific instance instead of default.
- xmpp: Split into ejabberd and jsxc modules.
- users: Moved part of LDAP setup to first-run.

## [0.12.0] - 2016-12-08
### Added
- Added screenshots to Readme.
- repro: Open up RTP ports.
- Allow modules to register steps for first_boot.
- frontpage: Show Configure button in service details, when user is logged in.
- minetest: Add mods packages to be installed with server.
- networks: Support configuring IPv6 networks.

### Fixed
- Upstream patch from Debian bug #837206 to fix DB and log file
  permissions. Also switch to new setup command.
- Include module static files in build, required for Debian package build.
- dynamicdns: Allow reading status as non-root.
- config: Set current domainname again after hostname change.
- config: Handle clearing of domain name.
- letsencrypt: When no domains are configured, show better message,
  and hide diagnostics button.
- frontpage: Fix shortcut spacing issue.
- xmpp: Updated to work with JSXC 3.0.0.

### Changed
- repro: Use firewalld provided SIP services.
- xmpp: Show more clearly if domain is not set.
- frontpage: Don't show apps requiring login, unless logged in.
- ttrss: Show status block.
- frontpage: Make app icons larger.
- frontpage: Center shortcut text under icons.
- frontpage: Move info to bottom and center.
- firewall: Only show services that have completed setup.
- firewall: Collapse port lists so they are hidden by default.
- users: Make it harder to accidentally delete the only Plinth user.

## [0.11.0] - 2016-09-21
### Added
- Added loading icon for other busy operations.
- Added basic front page with shortcuts to web apps, and information
  about enabled services.
- Allow initial setup operation to happen without package
  installation.
- networks: Add polkit rules for network management.
- Update man page to add setup operations.
- Add argument to list packages needed by apps.
- networks: Add batctl as dependency.

### Fixed
- users: Fixed checking restricted usernames.
- users: Display error message if unable to set SSH keys.
- help: Minor updates and fixes to status log.
- Updated translations to fix weblate errors.
- Fixed spelling errors in datetime and letsencrypt modules.
- users: Flush nscd cache after user operations.
- monkeysphere: Adopted to using SHA256 fingerprints.
- monkeysphere: Sort items for consistent display.
- monkeysphere: Handle new uid format of gpg2.
- monkeysphere: Fixed handling of unavailable imported domains.
- minetest: Fixed showing status block and diagnostics.
- Fix stretched favicon.

### Changed
- dynamicdns, monkeysphere, transmission, upgrades: Use actions where
  root is required, so that Plinth can run as non-root.
- xmpp: Switched to using ruamel.yaml to modify ejabberd config.
- Exit with error if any of the setup steps fail.
- actions: Hush some unneeded output of systemd.
- letsencrypt: Depend on the new certbot package.
- Switch base template from container-fluid to container. This will
  narrow the content area for larger displays.
- Readjust the responsive widths of various tables.
- Print django migrate messages only in debug.
- Tune log message verbosity.
- Plinth no longer runs as root user.  Fix all applications that were
  requiring root permission.
- xmpp: Replace jwchat with jsxc. Bump module version number so
  current installs can be updated.
- ikiwiki: Allow only alphanumerics in wiki/blog name.

### Removed
- Remove width management for forms.

## [0.10.0] - 2016-08-12
### Added
- Added Disks module to show free space of mounted partitions and
  allow expanding the root partition.
- Added Persian (fa) locale.
- Added Indonesian (id) locale.
- Added options to toggle Tor relay and bridge relay modes.
- Added Security module to control login restrictions.
- Added a page to display recent status log from Plinth. It is
  accessible from the 500 error page.
- networks: Added ability to configure generic interfaces.
- networks: Added 'disabled' IPv4 method.
- networks: Added configuration of wireless BSSID, band, and channel.
- networks: Added NetworkManager dispatcher script to configure
  batman-adv mesh networking.
- radicale: Added access rights control.
- tor: Added spinner when configuration process is ongoing.
- Allowed --setup command to take a list of modules to setup.
- Added Vagrantfile.
- Added Snapshots module to manage Btrfs snapshots.

### Removed
- networks: Removed hack for IP address fetching.

### Fixed
- Improved Dynamic DNS status message when no update needed.
- Improved Ikiwiki description.
- Added check if a2query is installed before using it, since apache2
  is not a dependency for Plinth.
- networks: Fixed incorrect access for retrieving DNS entries.
- Fixed issue with lost menus in Django 1.10.
- Added workaround for script prefix problem in stronghold.
- users: Fixed editing users without SSH keys.

### Changed
- Added suggested packages for ikiwiki. Removed recommends since they
  are installed automatically.
- users: Switched to using dpkg-reconfigure to configure several
  packages. This will work even if the package is already installed.
- Bumped required version of Django to 1.10.

## [0.9.4] - 2016-06-14
### Fixed
- Fixed quoted values in nslcd config.

## [0.9.3] - 2016-06-12
### Added
- Added Polish translation.
- Added check to Diagnostics to skip tests for modules that have not
  been setup.
- Added sorting of menu items per locale.
- Allowed setting IP for shared network connections.

### Fixed
- Fixed issue preventing access to Plinth on a non-standard port.
- Fixed issue in Privoxy configuration. Two overlapping
  listen-addresses were configured, which prevented privoxy service
  from starting.
- Fixed issues with some diagnostic tests that would show false
  positive results.
- Fixed some username checks that could cause errors when editing the
  user.
- Switched to using apt-get for module setup in Plinth. This fixes
  several issues that were seen during package installs.

### Changed
- Moved Dynamic DNS and Pagekite from Applications to System
  Configuration.

### Deprecated
- Dealt with ownCloud removal from Debian. The ownCloud page in Plinth
  will be hidden if it has not been setup. Otherwise, a warning is
  shown.

### Removed
- Removed init script and daemonize option.
- Removed writing to PID file.

### Security
- Fixed issue that could allow someone to start a module setup process
  without being logged in to Plinth.

[0.14.0]: https://github.com/freedombox/Plinth/compare/v0.13.1...v0.14.0
[0.13.1]: https://github.com/freedombox/Plinth/compare/v0.13.0...v0.13.1
[0.13.0]: https://github.com/freedombox/Plinth/compare/v0.12.0...v0.13.0
[0.12.0]: https://github.com/freedombox/Plinth/compare/v0.11.0...v0.12.0
[0.11.0]: https://github.com/freedombox/Plinth/compare/v0.10.0...v0.11.0
[0.10.0]: https://github.com/freedombox/Plinth/compare/v0.9.4...v0.10.0
[0.9.4]: https://github.com/freedombox/Plinth/compare/v0.9.3...v0.9.4
[0.9.3]: https://github.com/freedombox/Plinth/compare/v0.9.2...v0.9.3
