.. SPDX-License-Identifier: CC-BY-SA-4.0

Part 7: Other Changes
---------------------

Creating diagnostics
^^^^^^^^^^^^^^^^^^^^

When the app does not work as expected, the user should know what is happening
with the app. FreedomBox framework provides an API for running and showing
diagnostics results. Most of the common diagnostic tests are implemented by the
framework as part of the components used by an app. FreedomBox takes care of
calling the diagnostics method and displaying the list in a formatted manner.

To implement additional diagnostic tests on top of those provided by the
framework, the method :meth:`plinth.app.App.diagnose` has to be overridden or in
a component that belongs to the app, the method
:meth:`plinth.app.Component.diagnose` has to be overridden. The methods must
return a list in which each item is the result of a test performed. The item
itself is a two-tuple containing the display name of the test followed by the
result as ``passed``, ``failed`` or ``error``.

.. code-block:: python3
  :caption: ``views.py``

  class TransmissionAppView(views.AppView):
      ...
      def diagnose():
          """Run diagnostics and return the results."""
          results = super().diagnose()

          results.append(['Example test', 'passed'])

          return results

The user can trigger the diagnostics test by going to **System -> Diagnostics**
page. This runs diagnostics for all the applications. Users can also run
diagnostics specifically for this app from the app's page. A diagnostics menu
item is shown by the :class:`plinth.views.AppView` and `app.html` template
automatically when ``diagnose()`` method is overridden in the app or a
component.

Logging
^^^^^^^

Sometimes we may feel the need to write some debug messages to the console and
system logs. Doing this in FreedomBox is just like doing this any other Python
application.

.. code-block:: python3
  :caption: ``views.py``

  import logging

  logger = logging.getLogger(__name__)

  def example_method():
      logger.debug('A debug level message')

      logger.info('Showing application page - %s', request.method)

      try:
          something()
      except Exception as exception:
          # Print stack trace
          logger.exception('Encountered an exception - %s', exception)

For more information see Python :doc:`logging framework <howto/logging>`
documentation.

Internationalization
^^^^^^^^^^^^^^^^^^^^

Every string message that is visible to the user must be localized to user's
native language. For this to happen, our app needs to be internationalized. This
requires marking the user visible messages for translation. FreedomBox apps use
the Django's localization methods to make that happen.

.. code-block:: python3
  :caption: ``__init__.py``

  from django.utils.translation import gettext_lazy as _

  class TransmissionApp(app_module.App):
      ...

      def __init__(self):
        ...

        info = app_module.Info(...
                               name=_('Transmission'),
                               description=[_('Transmission is a...'),
                                            _('BitTorrent is a peer-to-peer...')],
                               ...
                               tags=[_('File sharing'), _('BitTorrent'), ...])
                               ...)

Notice that the app's name, description, tags, etc. are wrapped in the ``_()``
method calls. This needs to be done for the rest of our app. We use the
:obj:`~django.utils.translation.gettext_lazy` in some cases and we use the
regular :obj:`~django.utils.translation.gettext` in other cases. This is because
in the second case the :obj:`~django.utils.translation.gettext` lookup is made
once and reused for every user looking at the interface. These users may each
have a different language set for their interface. Lookup made for one language
for a user should not be used for other users. The ``_lazy`` methods provided by
Django makes sure that the return value is an object that will actually be
converted to string at the final moment when the string is being displayed. In
the first case, the lookup is made and string is returned immediately.

All of this is the usual way internationalization is done in Django. See
:doc:`Internationalization and localization <django:topics/i18n/index>`
documentation for more information.
