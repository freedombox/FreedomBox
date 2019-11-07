.. SPDX-License-Identifier: CC-BY-SA-4.0

Part 5: Customizing
-------------------

Customizing the application page
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The view that we have written above requires a template file. A default template
file is provided by the framework. In some cases, we will need to customize this
template. Let us create a custom template file in ``transmission.html``.

.. code-block:: django

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

  class TransmissionAppView(AppView):
      ...
      template_name = 'transmission.html'

Writing a configuration form
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Our app needs some configuration. So, we need to write a configuration form to
provide options to the user. Add the following to ``forms.py``.

.. code-block:: python3

  from django import forms

  from plinth.forms import AppForm


  class TransmissionForm(AppForm):  # pylint: disable=W0232
      """Transmission configuration form"""
      download_dir = forms.CharField(
          label='Download directory',
          help_text='Directory where downloads are saved.  If you change the '
                    'default directory, ensure that the new directory exists '
                    'and is writable by "debian-transmission" user.')

This creates a Django form that shows a single option to set the download
directory for our Transmission app. This is how a regular Django form is built.
See :doc:`Django Forms documentation <django:topics/forms/index>` for more
information.

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

  from django.contrib import messages

  from plinth import actions, views

  from .forms import TransmissionForm

  class TransmissionAppView(views.AppView):
      ...
      form_class = TransmissionForm

      def get_initial(self):
          """Get the current settings from Transmission server."""
          status = super().get_initial()
          configuration = actions.superuser_run('transmission',
                                                ['get-configuration'])
          configuration = json.loads(configuration)
          status.update({
              key.translate(str.maketrans({
                  '-': '_'
              })): value
              for key, value in configuration.items()
          })
          return status

      def form_valid(self, form):
          """Apply the changes submitted in the form."""
          old_status = form.initial
          new_status = form.cleaned_data

          if old_status['download_dir'] != new_status['download_dir']:
              new_configuration = {
                  'download-dir': new_status['download_dir'],
              }

              actions.superuser_run('transmission', ['merge-configuration'],
                                    input=json.dumps(new_configuration).encode())
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

Writing actions
^^^^^^^^^^^^^^^

The actual work of performing the configuration change is carried out by an
*action*. Actions are independent scripts that run with higher privileges
required to perform a task. They are placed in a separate directory and invoked
as scripts via sudo. For our application we need to write an action that can
enable and disable the web configuration. We will do this by creating a file
``actions/transmission``.

.. code-block:: python3

  import argparse
  import json
  import sys

  from plinth import action_utils

  TRANSMISSION_CONFIG = '/etc/transmission-daemon/settings.json'


  def parse_arguments():
      """Return parsed command line arguments as dictionary."""
      parser = argparse.ArgumentParser()
      subparsers = parser.add_subparsers(dest='subcommand', help='Sub command')

      subparsers.add_parser('get-configuration',
                            help='Return the current configuration')
      subparsers.add_parser(
          'merge-configuration',
          help='Merge JSON configuration from stdin with existing')

      subparsers.required = True
      return parser.parse_args()


  def subcommand_get_configuration(_):
      """Return the current configuration in JSON format."""
      configuration = open(TRANSMISSION_CONFIG, 'r').read()
      print(configuration)


  def subcommand_merge_configuration(arguments):
      """Merge given JSON configuration with existing configuration."""
      configuration = sys.stdin.read()
      configuration = json.loads(configuration)

      current_configuration = open(TRANSMISSION_CONFIG, 'r').read()
      current_configuration = json.loads(current_configuration)

      new_configuration = current_configuration
      new_configuration.update(configuration)
      new_configuration = json.dumps(new_configuration, indent=4, sort_keys=True)

      open(TRANSMISSION_CONFIG, 'w').write(new_configuration)
      action_utils.service_reload('transmission-daemon')


  def main():
      """Parse arguments and perform all duties."""
      arguments = parse_arguments()

      subcommand = arguments.subcommand.replace('-', '_')
      subcommand_method = globals()['subcommand_' + subcommand]
      subcommand_method(arguments)


  if __name__ == '__main__':
      main()

This is a simple Python3 program that parses command line arguments. While
Python3 is preferred, it can be written in other languages also. It may use
various helper utilities provided by the FreedomBox framework in
:obj:`plinth.action_utils` to easily perform it's duties.

This script is automatically installed to ``/usr/share/plinth/actions`` by
FreedomBox's installation script ``setup.py``. Only from here will there is a
possibility of running the script under ``sudo``. If you are writing an
application that resides indenpendently of FreedomBox's source code, your app's
``setup.py`` script will need to take care of copying the file to this target
location.
