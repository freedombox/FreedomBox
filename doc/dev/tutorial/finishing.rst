.. SPDX-License-Identifier: CC-BY-SA-4.0

Part 8: Finishing
-----------------

Adding a License
^^^^^^^^^^^^^^^^

FreedomBox is licensed under the GNU Affero General Public License Version 3 or
later. FreedomBox apps, which run as modules under FreedomBox Service (Plinth),
also need to be under the same license or under a compatible license. The
license of our app needs to clear for our app to be accepted by users and other
developers. Let us add license headers to our application.

.. code-block:: python3

  #
  # This file is part of FreedomBox.
  #
  # This program is free software: you can redistribute it and/or modify
  # it under the terms of the GNU Affero General Public License as
  # published by the Free Software Foundation, either version 3 of the
  # License, or (at your option) any later version.
  #
  # This program is distributed in the hope that it will be useful,
  # but WITHOUT ANY WARRANTY; without even the implied warranty of
  # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  # GNU Affero General Public License for more details.
  #
  # You should have received a copy of the GNU Affero General Public License
  # along with this program.  If not, see <http://www.gnu.org/licenses/>.
  #

The above header needs to be present in every file of the application. It is
suitable for Python files. However, in template files, we need to modify it
slightly.

.. code-block:: django

  {% extends "base.html" %}
  {% comment %}
  #
  # This file is part of FreedomBox.
  #
  # This program is free software: you can redistribute it and/or modify
  # it under the terms of the GNU Affero General Public License as
  # published by the Free Software Foundation, either version 3 of the
  # License, or (at your option) any later version.
  #
  # This program is distributed in the hope that it will be useful,
  # but WITHOUT ANY WARRANTY; without even the implied warranty of
  # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  # GNU Affero General Public License for more details.
  #
  # You should have received a copy of the GNU Affero General Public License
  # along with this program.  If not, see <http://www.gnu.org/licenses/>.
  #
  {% endcomment %}

Coding standards
^^^^^^^^^^^^^^^^

For readability and easy collaboration it is important to follow common coding
standards. FreedomBox uses the Python coding standards and uses the ``pylint``
and ``flake8`` tools to check if the there are any violations. Run these tools
on our application and fix any errors and warnings. Better yet, integrate these
tools into your favorite IDE for on-the-fly checking.

For the most part, the code we have written so far, is already compliant with
the coding standards. This includes variable/method naming, indentation,
document strings, comments, etc. One thing we have to add are the module
documentation strings. Let us add those. In ``__init__.py`` add the top:

.. code-block:: python3

  """
  FreedomBox app to configure Transmission.
  """

Contributing code to FreedomBox
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``HACKING.md`` and ``CONTRIBUTING.md`` files in the FredomBox source code
have tips on how to contribute code to the project. Be sure to read them if you
are submitting your app for including on the project.

Here is ``HACKING.md``:

.. literalinclude:: ../../../HACKING.md
   :language: md

Here is ``CONTRIBUTING.md``:

.. literalinclude:: ../../../CONTRIBUTING.md
   :language: md
