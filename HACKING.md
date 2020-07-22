# Hacking

## Requirements for Development OS

FreedomBox is built as part of Debian GNU/Linux. However, you don't need to
install Debian to do development for FreedomBox. FreedomBox development is
typically done on a container or a Virtual Machine.

For running a container, you need systemd containers, Git, Python and a
sudo-enabled user. This approach is recommended.

For running a VM, you can work on any operating system that can install latest
versions of Git, Vagrant and VirtualBox.

## Using Containers

The ./container script shipped with FreedomBox source code can manage the
development environment inside a systemd-nspawn container.

1.  Checkout FreedomBox Service (Plinth) source code using Git:

    ```bash
    host$ git clone https://salsa.debian.org/freedombox-team/freedombox.git
    host$ cd freedombox
    ```

2.  Work in a specific branch:
    ```bash
    host$ git branch YOUR-FEATURE-BRANCH`
    host$ git checkout YOUR-FEATURE-BRANCH`
    ```

3.  To download, setup, run, and configure a container for FreedomBox
    development, simply execute in your FreedomBox Service (Plinth) development
    folder:

    ```bash
    host$ ./container up
    ```

4.  SSH into the running container with the following command:

    ```bash
    host$ ./container ssh
    ```

### Using after Setup

After logging into the container, the source code is available in /freedombox
directory:

```bash
guest$ cd /freedombox
```

Run the development version of FreedomBox Service (Plinth) from your source
directory in the container using the following command. This command
continuously deploys your code changes into the container providing a
quick feedback cycle during development.

```bash
guest$ freedombox-develop
```

If you have changed any system configuration files during your development,
you will need to run the following to install those files properly on to the
system and their changes to reflect properly.

```bash
guest$ sudo ./setup.py install
```

Note: This development container has automatic upgrades disabled by default.

## Using Vagrant

Use VirtualBox and Vagrant if for some reason, the container option is not
suitable such as when you are running non-GNU/Linux machine or a non-systemd
machine.

### For Debian GNU/Linux and Derivatives

1. Install Git, Vagrant and VirtualBox using apt.

   ```bash
   $ sudo apt install git virtualbox vagrant
   ```

#### Installing VirtualBox manually

1. Add Oracle's key to apt's list of accepted keys.

   ```bash
   $ sudo wget -q https://www.virtualbox.org/download/oracle_vbox_2016.asc -O- | sudo apt-key add -
   ```

2. Create a file under /etc/apt/sources.list.d/ for virtualbox package.


   ```bash
   $ sudo touch /etc/apt/sources.list.d/virtualbox.list
   ```

3. Add the relevant source for your Debian/derivative distribution into the above file.

Example for Buster:
   ```
   deb https://download.virtualbox.org/virtualbox/debian buster contrib
   ```

4. Search and install the latest virtualbox package.

   ```bash
   $ apt search virtualbox

       # virtualbox-6.1
       # virtualbox-6.0

   $ sudo apt install virtualbox-6.1
   ```

### For Other GNU/Linux Distributions or *BSDs

1. Install Git, Vagrant and VirtualBox using your favourite package manager.

### For macOS

1. Install [Homebrew](https://brew.sh/).

2. Install Git, VirtualBox and Vagrant using Homebrew.

   ```bash
   $ brew install git
   $ brew cask install virtualbox
   $ brew cask install vagrant
   ```

### For Windows

1. Install [Git](https://git-scm.com/download/windows),
   [VirtualBox](https://www.virtualbox.org/wiki/Downloads) and
   [Vagrant](https://www.vagrantup.com/downloads.html) from their respective
   download pages.

2. Tell Git to use Unix line endings by running the following in Git Bash.

   ```bash
   host$ git config --global core.autocrlf input
   ```

3. Run all the following commands inside Git Bash.

### Setting Up Development Environment Using Vagrant

Vagrant is a free software command line utility for managing the life cycle of
virtual machines. The FreedomBox project provides ready-made virtual machines
(VMs) for use with Vagrant. These images make setting up an environment for
FreedomBox development rather simple: You can edit the source code on your host
and immediately see the effects in the running VM. The entire setup is automatic
and requires about 4.5 GB of disk space.

1.  Checkout FreedomBox Service (Plinth) source code using Git.

    ```bash
    host$ git clone https://salsa.debian.org/freedombox-team/freedombox.git
    host$ cd freedombox
    ```

2.  To download, setup, run, and configure a VM for FreedomBox development using
    Vagrant, simply execute in your FreedomBox Service (Plinth) development
    folder:

    ```bash
    host$ vagrant up
    ```

3.  SSH into the running vagrant box with the following command:

    ```bash
    host$ vagrant ssh
    ```

### Using the Virtual Machine

After logging into the virtual machine (VM), the source code is available in
/vagrant directory:

```bash
vm$ cd /vagrant
```

Run the development version of FreedomBox Service (Plinth) from your source
directory in the virtual machine using the following command. This command
continuously deploys your code changes into the virtual machine providing a
quick feedback cycle during development.

```bash
vm$ sudo -u plinth /vagrant/run --develop
```

If you have changed any system configuration files during your development,
you will need to run the following to install those files properly on to the
system and their changes to reflect properly.

```bash
vm$ sudo ./setup.py install
```

Note: This development virtual machine has automatic upgrades disabled by
default.

## Running Tests

To run all the tests in the container/VM:

```bash
guest$ py.test-3
```

Another way to run tests (not recommended):

```bash
guest$ ./setup.py test
```

To run a specific test function, test class or test module, use pytest filtering
options. See pytest documentation for further filter options.

**Examples:**

```bash
# Run tests in a directory
guest$ py.test-3 plinth/tests

# Run tests in a module
guest$ py.test-3 plinth/tests/test_actions.py

# Run tests of one class in test module
guest$ py.test-3 plinth/tests/test_actions.py::TestActions

# Run one test in a class or module
guest$ py.test-3 plinth/tests/test_actions.py::TestActions::test_is_package_manager_busy
```

## Running the Test Coverage Analysis

To run the coverage tool in the container/VM:

```bash
guest$ py.test-3 --cov=plinth
```

To collect HTML report:

```bash
guest$ py.test-3 --cov=plinth --cov-report=html
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

#### For running tests inside the container

Inside the container run

```bash
guest$ cd /freedombox ; sudo plinth/tests/functional/install.sh
```

#### For running tests inside the VM

From the host, provision the virtual machine with tests:

```bash
host$ vagrant provision --provision-with tests
```

#### For running tests on host machine

Follow the instructions below to run the tests on host machine. If you wish
perform the tests on host machine, the host machine must be based on Debian
Buster (or later).

```bash
host$ pip3 install splinter
host$ pip3 install pytest-splinter
host$ pip3 install pytest-xdist  # optional, to run tests in parallel
host$ sudo apt install firefox
host$ sudo apt install python3-pytest-bdd
host$ sudo apt install xvfb python3-pytest-xvfb  # optional, to avoid opening browser windows
host$ sudo apt install smbclient  # optional, to test samba
```

- Install the latest version of geckodriver. It is usually a single binary which
  you can place at /usr/local/bin/geckodriver . Geckodriver will use whichever
  binary is named 'firefox' for launching the browser and interacting with it.

### Run FreedomBox Service

*Warning*: Functional tests will change the configuration of the system
 under test, including changing the hostname and users. Therefore you
 should run the tests using FreedomBox running on a throw-away VM.

The VM should have NAT port-forwarding enabled so that 4430 on the
host forwards to 443 on the guest. From where the tests are running, the web
interface of FreedomBox should be accessible at https://localhost:4430/.

To run samba tests, port 4450 on the host should be forwarded to port 445
on the guest.

### Setup FreedomBox Service for tests

Via Plinth, create a new user as follows:

* Username: tester
* Password: testingtesting

This step is optional if a fresh install of Plinth is being tested. Functional
tests will create the required user using FreedomBox's first boot process.

### Run Functional Tests

**When inside a container/VM you will need to target the guest**

```bash
guest$ export FREEDOMBOX_URL=https://localhost FREEDOMBOX_SAMBA_PORT=445
```

You will be running `py.test-3`.

```bash
guest$ py.test-3 --include-functional
```

The full test suite can take a long time to run (more than an hour). You can
also specify which tests to run, by specifying a mark:

```bash
guest$ py.test-3 -m essential --include-functional
guest$ py.test-3 -m mediawiki --include-functional
```

If xvfb is installed and you still want to see browser windows, use the
`--no-xvfb` command-line argument.

```bash
guest$ py.test-3 --no-xvfb -m mediawiki --include-functional
```

Tests can also be run in parallel, provided you have the pytest-xdist plugin
installed.

```
$ py.test-3 -n 4 --dist=loadfile --include-functional -m essential
```

## Building the Documentation Separately

FreedomBox Service (Plinth) man page is built from DocBook source in the `doc/`
directory. FreedomBox manual is downloaded from the wiki is also available
there. Both these are build during the installation process.

To build the documentation separately, run:

```bash
guest$ make -C doc
```

## Repository

FreedomBox Service (Plinth) is available from
[salsa.debian.org](https://salsa.debian.org/freedombox-team/freedombox).

## Bugs & TODO

You can report bugs on FreedomBox Service's (Plinth's) [issue
tracker](https://salsa.debian.org/freedombox-team/freedombox/issues).

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

## Application Icons

When adding a new App into FreedomBox, an icon is needed to represent the app in
the application view and for shortcuts in the front page. The following the
guidelines for creating an app icon:

- Use SVG format.
- Keep the size and complexity of the SVG minimal. Simplify the graphic if
  necessary.
- Units for the entire document should be in pixels.
- View area should be 512x512 pixels.
- Background should be transparent.
- Leave no margins and prefer a square icon. If the icon is wide, leave top and
  bottom margins. If the icon is tall, leave left and right margins.
