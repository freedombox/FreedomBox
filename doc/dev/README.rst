.. SPDX-License-Identifier: CC-BY-SA-4.0

Editing the Developer Documentation
===================================

About
*****

The doc/dev directory in FreedomBox repository contains the FreedomBox Developer
Manual. Specifically the tutorial for writing new applications and API reference
for writing apps for FreedomBox. It is kept as part of the main FreedomBox
source code with the expectation that when the API changes the developer
documentation is also updated in the same patch set.

Setup on Debian
***************

Install the following Debian packages:

* python3-sphinx
* python3-sphinx-autobuild
* python3-django
* python3-django-axes
* python3-django-captcha
* python3-django-ipware
* python3-django-stronghold

If your preferred text editor doesn't have support for the reStructuredText
format, you can install a simple desktop application called ReText. It has live
preview support with split panes.

Viewing changes live in your browser
************************************

You do not need the virtual machine used for FreedomBox development running to
edit this documentation.

Run `make livehtml` from the current directory in the host machine. Visit
http://127.0.0.1:8000 to view the changes live in your browser as you edit the
.rst files in this directory. Your browser reloads the page automatically each
time you save an .rst file in the documentation.
