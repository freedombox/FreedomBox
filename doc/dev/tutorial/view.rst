.. SPDX-License-Identifier: CC-BY-SA-4.0

Part 3: View
------------

Writing the URLs
^^^^^^^^^^^^^^^^

For a user to visit our app in FreedomBox, we need to provide a URL. When the
user visits this URL, a view is executed and a page is displayed. In ``urls.py``
write the following:

.. code-block:: python3
  :caption: ``urls.py``

  from django.urls import re_path

  from .views import TransmissionAppView

  urlpatterns = [
      re_path(r'^apps/transmission/$', TransmissionAppView.as_view(), name='index'),
  ]

This routes the ``/apps/transmission/`` URL to a view called
``TransmissionAppView`` defined in ``plinth/modules/transmission/views.py``.
This is no different than how routing URLs is done in Django. See :doc:`Django
URL dispatcher <django:topics/http/urls>` for more information.

Adding a menu item
^^^^^^^^^^^^^^^^^^

We have added a URL to be handled by our app but this does not yet show up to be
a link in FreedomBox web interface. Let us add a link in the apps list. In
``__init__.py`` add the following:

.. code-block:: python3
  :caption: ``__init__.py``

  from plinth import menu

  class TransmissionApp(app_module.App):
      ...

      def __init__(self):
          ...

          menu_item = menu.Menu('menu-transmission', 'Transmission',
                                'BitTorrrent Web Client', 'transmission',
                                'transmission:index', parent_url_name='apps')
          self.add(menu_item)

What this does is add a menu item component into the our app. In FreedomBox
framework, an app is made up of many simple components. When operations such as
enable/disable are performed on the app, they will be applied on all the
components. In case of menu components, FreedomBox framework takes care of
presenting them appropriately. The component captures various details about the
menu item we want to present.

* The first parameter is simply a unique ID for the component.

* The second parameter is the display name to use for our menu item which
  happens to be the name of the app as well.

* The third parameter is a short description for the menu item.

* The fourth parameter is the name of the icon to use when showing the menu
  item. An SVG file and a PNG should be created in the
  ``plinth/modules/transmission/static/icons/`` directory.

* The fifth parameter is the URL that the user should be directed to when the
  menu item is clicked. This is a Django URL name and we have already created a
  URL with this name. Note that when including our app's URLs, FreedomBox will
  automatically set the name of the module as the Django URL namespace. Hence it
  is ``transmission:index`` and not just ``index``.

* We wish to add our menu item to the list of apps in the apps page which is why
  we have specified ``apps`` as the parent URL for the this app in the final
  parameter.

Writing a view
^^^^^^^^^^^^^^

We have a URL pointing to our view. We have also added a menu item in the apps
section of the web interface that points to our view. We now need to create a
view to show the app page for our app. In ``views.py``, let us add a view.

.. code-block:: python3
  :caption: ``views.py``

  from plinth import views
  from plinth.modules import transmission

  class TransmissionAppView(views.AppView):
      """Serve configuration page."""
      app_id = 'transmission'

The base view :class:`~plinth.views.AppView` takes care of a lot of details for
us. First, it shows basic information about the app like name, description,
desktop/mobiles clients for the service (described later), link to the manual
page (described later), link to diagnostics button, etc. Then it shows the
status of the app whether it is running and can also present a form for
configuration. It also presents a way to enable/disable the app.
