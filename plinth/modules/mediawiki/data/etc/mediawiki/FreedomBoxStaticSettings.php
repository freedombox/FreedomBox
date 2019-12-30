<?php
/*
 This file is shipped by FreedomBox to manage static settings. Newer versions of
 this file are shipped by FreedomBox and are expected to override this file
 without any user prompts. It should not be modified by the system
 administrator. Additional setting modified by FreedomBox at placed in
 FreedomBoxSettings.php. No newer version of that file is ever shipped by
 FreedomBox.
*/

# Default logo
$wgLogo = "$wgResourceBasePath/resources/assets/mediawiki.png";

# Enable file uploads
$wgEnableUploads = true;

# Public registrations
$wgGroupPermissions['*']['createaccount'] = false;

# Read/write permissions for anonymous users
$wgGroupPermissions['*']['edit'] = false;
$wgGroupPermissions['*']['read'] = true;

# Short urls
$wgArticlePath = "/mediawiki/$1";
$wgUsePathInfo = true;

# Instant Commons
$wgUseInstantCommons = true;

# SVG Enablement
$wgFileExtensions[] = 'svg';
$wgAllowTitlesInSVG = true;
$wgSVGConverter = 'ImageMagick';

# Fix issue with session cache preventing logins, #1736
$wgSessionCacheType = CACHE_DB;
