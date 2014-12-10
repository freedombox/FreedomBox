% Plinth User Manual

# Introduction

## Name

plinth - a web front end for administering every aspect of a Freedom Box.

## Description

The Freedom Box is a net appliance conceived by Eben Moglen.  It
contains free software and is designed to allow you to interface with
the rest of the net under conditions of protected privacy and data
security.

The Plinth front end is a web interface to administer the functions of
the Freedom Box.  For example, the Freedom Box is a wireless router,
and the front end is where you can adjust its settings.

## Overview

The front end is an extensible web platform for forms and menus.  It
allows authenticated users to fill out forms.  The interface saves the
form data and from them generates configuration files for the various
services running on the box.

The interface is pluggable.  Drop modules into place to add new
capabilities to Plinth and your Freedom Box.  Replace existing modules
to get newer, better shinier functions.  The modules will
automatically integrate into the existing menu system so you can
control all of the box's parts from one central location.

## Getting Started

See the INSTALL file for additional details and dependencies. To install run:

    $ sudo python3 setup.py install

Run Plinth on the local system with:

    $ sudo plinth

## Contributing

See the HACKING file for contributing to Plinth.
