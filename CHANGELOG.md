# Change Log
All notable changes to this project will be documented in this file.

## [Unreleased]
### Added
- Added Disks module to show free space of mounted partitions and
  allow expanding the root partition.
- Added Persian (fa) locale.
- Added Indonesian (id) locale.
- Added options to toggle Tor relay and bridge relay modes.
- Added Security module to control login restrictions.
- Added a page to display recent status log from Plinth. It is
  accessible from the 500 error page.

### Fixed
- Improved Dynamic DNS status message when no update needed.
- Improved Ikiwiki description.

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

[Unreleased]: https://github.com/freedombox/Plinth/compare/v0.9.4...HEAD
[0.9.4]: https://github.com/freedombox/Plinth/compare/v0.9.3...v0.9.4
[0.9.3]: https://github.com/freedombox/Plinth/compare/v0.9.2...v0.9.3
