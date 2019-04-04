# Hacking

## Setting Up Development Environment Using Vagrant

Vagrant is a free software command line utility for managing the life cycle of
virtual machines. The FreedomBox project provides ready-made virtual machines
(VMs) for use with Vagrant. These images make setting up an environment for
FreedomBox development rather simple: You can edit the source code on your host
and immediately see the effects in the running VM. The entire setup is automatic
and requires about 4.5 GB of disk space.

1.  Install Vagrant and VirtualBox:

    ```
    $ sudo apt-get install virtualbox vagrant
    ```

2.  To download, setup, run, and configure a VM for FreedomBox development using
    Vagrant, simply execute in your FreedomBox Service (Plinth) development
    folder:

    ```
    $ vagrant up
    ```

3. SSH into the running vagrant box with the following command:
    ```
    $ vagrant ssh
    ```

4. Run the development version of Plinth from your source directory in the
   virtual machine using the following command. This command continuously
   deploys your code changes into the virtual machine providing a quick feedback
   cycle during development.

    ```
    $ sudo -u plinth /vagrant/run --develop
    ```

Note: This virtual machine has automatic upgrades disabled by default.


## Manually Setting Up for Development

It is recommended that you use Vagrant to setup your development environment.
However, for some reason, you wish setup manually, the following tips will help:

1.  Install dependencies as follows:

    ```
    $ sudo apt build-dep .
    ```

    ```
    $ sudo apt install -y $(./run --list-dependencies)
    ```

    Install additional dependencies by picking the list from debian/control file
    fields Depends: and Recommends: for the package ''freedombox''.

2.  Instead of running `setup.py install` after every source modification, run
    the following command:

    ```
    $ sudo python3 setup.py develop
    ```

    This will install the python package in a special development mode.  Run it
    normally.  Any updates to the code (and core package data files) do not
    require re-installation after every modification.

    CherryPy web server also monitors changes to the source files and reloads
    the server as soon as a file is modified.  Hence it is usually sufficient
    to modify the source and refresh the browser page to see the changes.

2.  FreedomBox Service (Plinth) also supports running without installing (as much
    as possible). Simply run it as:

    ```
    $ sudo ./run --develop
    ```

    In this mode, FreedomBox Service (Plinth) runs from the working directory
    without need for installation. The server restarts automatically when any
    python file changes.  The `plinth.conf` config file and the action
    scripts of the working directory are used. It creates all that data and
    runtime files in `data/var/*`.
    More extensive debugging is enabled, Django security features are disabled
    and module initialization errors will not pass silently.

    *Note:* This mode is supported only in a limited manner.  The following are
    the unknown issues with it:

     1. Help pages are also not built. Run `make -C doc` manually.

     2. Actions do not work when running as normal user without `sudo` prefix.
        You need to add `actions` directory to be allowed for `sudo` commands.
        See `data/etc/sudoers.d/plinth` for a hint.

### Testing Inside a Virtual Machine

1.  Checkout source on the host.

2.  Share the source folder and mount it on virtual machine.  This could be done
    over NFS, SSH-fs or 'Shared Folders' feature on VirtualBox.

3.  Run `setup.py develop` or `setup.py install` as described above on guest
    machine.

4.  Access the guest machine's FreedomBox web UI from host after setting bridging
    or NATing for guest virtual machine.

## Running Tests

To run all the tests:

```bash
$ py.test-3
```

Another way to run tests (not recommended):

```bash
$ ./setup.py test
```

To run a specific test function, test class or test module, use pytest filtering
options.

**Examples:**

```bash
# Run tests in a directory
$ py.test-3 plinth/tests

# Run tests in a module
$ py.test-3 plinth/tests/test_actions.py

# Run tests of one class in test module
$ py.test-3 plinth/tests/test_actions.py::TestActions

# Run one test in a class or module
$ py.test-3 plinth/tests/test_actions.py::TestActions::test_is_package_manager_busy
```

## Running the Test Coverage Analysis

To run the coverage tool:

```
$ py.test-3 --cov=plinth
```

To collect HTML report:

```
$ py.test-3 --cov=plinth --cov-report=html
```

Invoking this command generates a HTML report to the `htmlcov` directory.
`index.html` presents the coverage summary, broken down by module. Data columns
can be sorted by clicking on the column header. Clicking on the name of a
particular source file opens a page that displays the contents of that file,
with color-coding in the left margin to indicate which statements or branches
were executed via the tests (green) and which statements or branches were not
executed (red).

## Running Functional Tests

### Install Dependencies

**For running tests in the VM** run `vagrant provision --provision-with tests`.
Otherwise follow the instructions below.

```
$ pip3 install splinter
$ pip3 install pytest-splinter
$ pip3 install pytest-bdd
$ sudo apt install xvfb  # optional, to avoid opening browser windows
$ pip3 install pytest-xvfb  # optional, to avoid opening browser windows
```

- Install the latest version of geckodriver.
It's usually a single binary which you can place at /usr/local/bin/geckodriver

- Install the latest version of Mozilla Firefox.
Download and extract the latest version from the Firefox website and symlink the
binary named `firefox` to /usr/local/bin.

Geckodriver will then use whatever version of Firefox you symlink as
/usr/local/bin/firefox.

### Run FreedomBox Service

*Warning*: Functional tests will change the configuration of the system
 under test, including changing the hostname and users. Therefore you
 should run the tests using FreedomBox running on a throw-away VM.

The VM should have NAT port-forwarding enabled so that 4430 on the
host forwards to 443 on the guest. From where the tests are running, the web
interface of FreedomBox should be accessible at https://localhost:4430/.

### Setup FreedomBox Service for tests

Via Plinth, create a new user as follows:

* Username: tester
* Password: testingtesting

This step is optional if a fresh install of Plinth is being tested. Functional
tests will create the required user using FreedomBox's first boot process.

### Run Functional Tests

**When inside a VM you will need to target the guest VM**

```bash
export FREEDOMBOX_URL=https://localhost
```

You will be running `py.test-3`.

```
$ py.test-3 --include-functional
```

The full test suite can take a long time to run (more than an hour). You can
also specify which tests to run, by tag or keyword:

```
$ py.test-3 -k essential --include-functional
```

If xvfb is installed and you still want to see browser windows, use the
`--no-xvfb` command-line argument.

```
$ py.test-3 --no-xvfb -k mediawiki --include-functional
```

## Building the Documentation Separately

FreedomBox Service (Plinth) man page is built from DocBook source in the `doc/`
directory. FreedomBox manual is downloaded from the wiki is also available
there. Both these are build during the installation process.

To build the documentation separately, run:

```
$ make -C doc
```

## Repository

FreedomBox Service (Plinth) is available from
[salsa.debian.org](https://salsa.debian.org/freedombox-team/plinth).

## Bugs & TODO

You can report bugs on FreedomBox Service's (Plinth's) [issue
tracker](https://salsa.debian.org/freedombox-team/plinth/issues).

See CONTRIBUTING.md for information how to best contribute code.

## Internationalization

To mark text for translation, FreedomBox Service (Plinth) uses Django's
translation strings. A module should e.g. `from django.utils.translation import
ugettext as _` and wrap user-facing text with `_()`. Use it like this:

```python
message = _('Application successfully installed and configured.')
```

## Translations

The easiest way to start translating is with your browser, by using
[Weblate](https://hosted.weblate.org/projects/freedombox/plinth/).
Your changes will automatically get pushed to the code repository.

Alternatively, you can directly edit the `.po` file in your language directory
`Plinth/plinth/locale/` and create a pull request (see CONTRIBUTING.md).
In that case, consider introducing yourself on #freedombox IRC (irc.debian.org),
because some work may have been done already on the [Debian translators
discussion lists](https://www.debian.org/MailingLists/subscribe)
or the Weblate localization platform.

For more information on translations: https://wiki.debian.org/FreedomBox/Translate
