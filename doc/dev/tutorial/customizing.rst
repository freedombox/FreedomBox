.. SPDX-License-Identifier: CC-BY-SA-4.0

Part 5: Customizing
-------------------

Customizing the application page
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The view that we have written above requires a template file. A default template
file is provided by the framework. In some cases, we will need to customize this
template. Let us create a custom template file in ``transmission.html``.

.. code-block:: django
  :caption: ``templates/transmission.html``

  {% extends "app.html" %}

  {% load i18n %}

  {% block configuration %}

    {{ block.super }}

    <h3>{% trans "Custom Section" %}</h3>

    <p>
      {% blocktrans trimmed %}
        Custom paragraph content.
      {% endblocktrans %}
    </p>

  {% endblock %}

This template extends an existing template known as ``app.html``. This template
is available in FreedomBox core to provide all the basic layout, styling, menus,
JavaScript and CSS libraries required for a typical app view. We will override
the configuration area after inheriting from the app template and keep the rest
as is. ``{{ block.super }}`` adds back the overwritten content in the
``configuration`` block.

Yet again, there is nothing special about the way this template is written. This
is a regular Django template. See :doc:`Django Template documentation
<django:topics/templates>`.

For styling and UI components, FreedomBox uses the Twitter Bootstrap project.
See `Bootstrap documentation <http://getbootstrap.com/css/>`_ for reference.

To start using our custom template, we need to pass this to our view. In
``views.py``, add the following line:

.. code-block:: python3
  :caption: ``views.py``

  class TransmissionAppView(AppView):
      ...
      template_name = 'transmission.html'

Writing a configuration form
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Our app needs some configuration. So, we need to write a configuration form to
provide options to the user. Add the following to ``forms.py``.

.. code-block:: python3
  :caption: ``forms.py``

  from django import forms


  class TransmissionForm(DirectorySelectForm):  # pylint: disable=W0232
      """Transmission configuration form"""

      def __init__(self, *args, **kw):
          validator = DirectoryValidator(username=SYSTEM_USER,
                                         check_creatable=True)
          super().__init__(title=_('Download directory'),
                           default='/var/lib/transmission-daemon/downloads',
                           validator=validator, *args, **kw)

This uses a utility provided by the framework and creates a Django form that
shows a single option to set the download directory for our Transmission app.
This is similar to how a regular Django form is built. See :doc:`Django Forms
documentation <django:topics/forms/index>` for more information.

.. tip: Too many options

  Resist the temptation to create a lot of configuration options. Although this
  will put more control in the hands of the users, it will make FreedomBox less
  usable. FreedomBox is a consumer product. Our target users are not technically
  savvy and we have make most of the decisions on behalf of the user to make the
  interface as simple and easy to use as possible.

Applying the changes from the form
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The view we have created needs to display the form and process the form after
the user submits it. Let us implement that in ``views.py``.

.. code-block:: python3
  :caption: ``views.py``

  from django.contrib import messages

  from plinth import actions, views

  from .forms import TransmissionForm

  class TransmissionAppView(views.AppView):
      """Serve configuration page."""
      form_class = TransmissionForm
      app_id = 'transmission'

      def get_initial(self):
          """Get the current settings from Transmission server."""
          status = super().get_initial()
          configuration = privileged.get_configuration()
          status['storage_path'] = configuration['download-dir']
          status['hostname'] = socket.gethostname()

          return status

      def form_valid(self, form):
          """Apply the changes submitted in the form."""
          old_status = form.initial
          new_status = form.cleaned_data
          if old_status['storage_path'] != new_status['storage_path']:
              new_configuration = {
                  'download-dir': new_status['storage_path'],
              }
              privileged.merge_configuration(new_configuration)
              messages.success(self.request, 'Configuration updated')

          return super().form_valid(form)

We check to make sure that the configuration value has actually changed after
the form is submitted. Although FreedomBox's operations are idempotent, meaning
that running them twice will not be problematic, we still wish to avoid
unnecessary operations for the sake of speed.

We are actually performing the operation using *actions*. We will implement this
action a bit later.

After we perform the operation, we will show a message on the response page that
the action was successful or that nothing happened. We use the Django messaging
framework to accomplish this. See :doc:`Django messaging framework
<django:ref/contrib/messages>` for more information.

Writing privileged actions
^^^^^^^^^^^^^^^^^^^^^^^^^^

The actual work of performing the configuration change is carried out by
privileged actions. These actions are independent scripts that run with higher
privileges required to perform a task. They are placed in a separate python
module 'privileged.py' and invoked as regular methods. For our application we
need to write two privileged actions that can read and write the configuration
for transmission daemon. We will do this by creating a file ``privileged.py``.

.. code-block:: python3
  :caption: ``privileged.py``

  import json
  import pathlib
  from typing import Union

  from plinth import action_utils
  from plinth.actions import privileged

  _transmission_config = pathlib.Path('/etc/transmission-daemon/settings.json')


  @privileged
  def get_configuration() -> dict[str, str]:
      """Return the current configuration in JSON format."""
      return json.loads(_transmission_config.read_text(encoding='utf-8'))


  @privileged
  def merge_configuration(configuration: dict[str, Union[str, bool]]) -> None:
      """Merge given JSON configuration with existing configuration."""
      current_configuration = _transmission_config.read_bytes()
      current_configuration = json.loads(current_configuration)

      new_configuration = current_configuration
      new_configuration.update(configuration)
      new_configuration = json.dumps(new_configuration, indent=4, sort_keys=True)

      _transmission_config.write_text(new_configuration, encoding='utf-8')
      action_utils.service_reload('transmission-daemon')

This is a simple Python3 module but it runs in a separate process with superuser
privileges due to the :meth:`plinth.actions.privileged` decorator. All such
methods must have full type annotations for the method parameters. Further, the
parameters and return value must be JSON serializable. It may use various helper
utilities provided by the FreedomBox framework in :obj:`plinth.action_utils` to
easily perform it's duties.
