.. SPDX-License-Identifier: CC-BY-SA-4.0

Part 1: Beginning
-----------------

Before we begin
^^^^^^^^^^^^^^^

FreedomBox Service (Plinth) is a web interface built using Python3 and Django.
FreedomBox apps are simply Django applications within the project. Hence, for
the most part, writing a FreedomBox app is all about :doc:`writing a Django
application <django:intro/tutorial01>`.

You should start by reading the :doc:`Django tutorial <django:intro/index>`. All
the concepts described there are applicable for how FreedomBox and its apps are
be built.

Picking an app
^^^^^^^^^^^^^^

We must first, of course, pick an application to add to FreedomBox. For the
purpose of this tutorial, let us pick Transmission. Transmission daemon handles
Bitorrent file sharing. BitTorrent is a peer-to-peer file sharing protocol.

.. important:: Choosing an app

  When choosing an application we must make sure that it respects users'
  freedom and privacy. By choosing to use FreedomBox, users have explicitly made
  a choice to keep the data with themselves, to not provide privacy compromising
  data to centralized entities and to use Free Software that respects their
  Software Freedom. These are not properties of *some* of the applications in
  FreedomBox but all applications *must* adhere to these principles. Apps should
  not even ask the users questions to this effect, because users have already
  made a choice.

Packaging the application
^^^^^^^^^^^^^^^^^^^^^^^^^

Majority of the effort in creating an application for FreedomBox is to package
it for Debian and get it uploaded to Debian repositories. Going through the
process of packaging itself is outside the scope of this tutorial. It is,
however, well documented elsewhere. You should start at the `Debian Packaging
Portal <https://wiki.debian.org/Packaging>`_.

Debian packaging might seem like an unnecessary process that takes time with its
adherence to standards, review process, legal checks, etc. However, upon close
examination, one will find that without these steps the goals of the FreedomBox
project cannot be met. Some of the advantages of Debian packaging are listed
below:

* Legal check ensures that proprietary licensed code or code with bad licenses
  does not inadvertently creep in.

* Libraries have to be packaged separately easing security handling. When a
  security vulnerability is identified in a library, just the library will have
  to be updated and not all the applications that depend on it.

* Upgrades become smoother. The dependency handling of the packaging system,
  configuration handling tools, tools to deal with various types of well known
  files help with ensuring a proper upgrade.

* Collaborative maintenance teams ensure that the package is well cared for even
  if you get busy with other work and can't spend time on your package.
  Following standards and using common infrastructure is critical to enable this
  development methodology.
