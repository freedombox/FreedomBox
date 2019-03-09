<?php

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
