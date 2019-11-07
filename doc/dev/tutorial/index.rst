.. SPDX-License-Identifier: CC-BY-SA-4.0

=====================================
Tutorial: Writing Apps for FreedomBox
=====================================

This tutorial covers writing an app for FreedomBox. FreedomBox is a pure blend
of Debian with a web interface, that configures its apps. We shall discuss
various aspects of building an app for FreedomBox, by creating an example app.
The app that is discussed in the tutorial already available in FreedomBox so you
can also study it's full source code.

There are two parts to writing a FreedomBox app. First is to make sure that the
app is available as a Debian package uploaded to its repositories. This is the
majority of the work involved. However, if an app is already available in Debian
repositories, the whole task is simplified.. The second part of writing an app
for FreedomBox is to provide a thin web interface layer for configuring and
managing the app. This is done by extending FreedomBox's user interface to
provide visibility to the app and to let the user control its operations in a
highly simplified way. This layer is what we typically refer to as a 'FreedomBox
app'.

FreedomBox apps can either be distributed to the end user as part of FreedomBox
Service (Plinth) source code by submitting the apps to the project or they can
distributed independently. This tutorial covers writing an app that is meant to
be distributed as part of FreedomBox Service (Plinth). However, writing
independent FreedomBox apps is also very similar and most of this tutorial is
applicable.

.. note:: The term *App*

  The term app, in this tutorial, is used to mean multiple concepts. A service
  or an application available to end users in FreedomBox is a combination of
  Debian package and a web interface layer. The web interface layer is also
  called a FreedomBox app which is very similar to and built upon a Django
  application.

.. toctree::

   beginning
   skeleton
   view
   components
   customizing
   setup
   other
   finishing
   code
