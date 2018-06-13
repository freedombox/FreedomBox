# Installing FreedomBox Service (Plinth)

1.  Install the dependencies:

    On a Debian based system, run:

    ```
    $ sudo apt-get install \
    augeas-tools \
    dblatex \
    docbook-utils \
    e2fsprogs \
    fonts-lato \
    gettext \
    gir1.2-glib-2.0 \
    gir1.2-nm-1.0 \
    ldapscripts \
    libjs-bootstrap \
    libjs-jquery \
    libjs-modernizr \
    make \
    network-manager \
    ppp \
    pppoe \
    python3 \
    python3-apt \
    python3-augeas \
    python3-bootstrapform \
    python3-cherrypy3 \
    python3-configobj \
    python3-coverage \
    python3-django \
    python3-django-axes \
    python3-django-captcha \
    python3-django-stronghold \
    python3-gi \
    python3-psutil \
    python3-requests \
    python3-ruamel.yaml \
    python3-setuptools \
    xmlto
    ```

2. Install FreedomBox Service (Plinth):

    Unzip the source into a directory.  Change to the directory containing the
    program and run:

    ```
    $ sudo python3 setup.py install
    $ sudo apt install -y $(plinth --list-dependencies)
     ```

3.  Run FreedomBox Service (Plinth):

    ```
    $ sudo plinth
    ```

4.  Access FreedomBox UI:

    UI should be accessible at http://localhost:8000/plinth

# Note on Django version:

Django 1.11 is required to run FreedomBox Service (Plinth). You can check the
version by running:

```
$ django-admin --version
```

If apt-get provided django < 1.11, then follow the steps below:

1.  Uninstall older django versions:

    ```
    $ sudo apt-get remove python3-django python3-django-stronghold \
    python3-bootstrap
    ```

2.  Install Python3 pip:

    ```
    $ sudo apt-get install python3-pip
    ```

3.  Install django1.11 through pip:

    ```
    $ sudo pip3 install django django-bootstrap-form django-stronghold \
    django-axes django-simple-captcha --upgrade
    ```
