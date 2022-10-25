# Hacking

This document provides reference information for FreedomBox **contribution** hacking **procedures**:
1. [Picking a task to work on](#picking-a-task-to-work-on)
1. [Setting up and using development environments](#development-environments-setting-up-and-their-usage)
1. [Contributing translations + how to make/keep FreedomBox international](#makingkeeping-freedombox-international)
1. [Testing](#testing)
1. [Documentation](#documentation)
1. [Submitting your changes](#submitting-your-changes)
1. [Other related stuff](#miscelanea)

It doesn't cover architecture, design choices or other product internals.

## Picking a task to work on

You can report bugs on FreedomBox Service's (Plinth's) [issue
tracker](https://salsa.debian.org/freedombox-team/freedombox/issues).
Newcomers will find easy, self-contained tasks tagged as "beginner".

Source code for FreedomBox Service is available from
[salsa.debian.org](https://salsa.debian.org/freedombox-team/freedombox).

## Development environments: setting up and their usage

### Requirements for Development OS

FreedomBox is built as part of Debian GNU/Linux. However, you don't need to
install Debian to do development for FreedomBox. FreedomBox development is
typically done with a container or a Virtual Machine.

* To run a container, you need systemd containers, Git, Python3 and a
sudo-enabled user. This approach is recommended.
* To run a VM, you can work on any operating system that can install latest
versions of Git, Vagrant and VirtualBox.

In addition:

- To run code quality checks you need flake8 and yapf. These may be installed
  inside the container with Python3 and pip but installing them on host leads to
  smoother development experience.
- To update translation strings on the host machine, you need Django and gettext
  to be installed on host machine. These can be installed with Python3 and pip.
- You need Mumble voice chat software to participate in bi-weekly live
  development discussions.

### Using Containers

The `./container` script shipped with FreedomBox source code can manage the
development environment inside a systemd-nspawn container.

1.  Checkout FreedomBox Service (Plinth) source code using Git:

    ```bash
    host$ git clone https://salsa.debian.org/freedombox-team/freedombox.git
    host$ cd freedombox
    ```

1.  Work in a specific branch:
    ```bash
    host$ git branch YOUR-FEATURE-BRANCH
    host$ git checkout YOUR-FEATURE-BRANCH
    ```

1.  To download, setup, run, and configure a container for FreedomBox
    development, simply execute in your FreedomBox Service (Plinth) development
    folder: (This step requires at least 16GB of free disk space)

    ```bash
    host$ ./container up
    ```

1. To run unit tests:

    ```bash
    host$ ./container run-tests
    ```

1.  To run unit and functional tests for an app:

    ```bash
    host$ ./container run-tests --pytest-args -v --include-functional --splinter-headless plinth/modules/{app-name}
    ```

    Drop the option `--splinter-headless` if you want to see the tests running
    in browser windows. Not specifying a module in the above command would run
    functional tests for all the apps and also unit tests.

1.  SSH into the running container with the following command:

    ```bash
    host$ ./container ssh
    ```

1. The default distribution used by the container script is "testing", but you
   can choose a different distribution (e.g. "stable") in two ways.

   1. Using an environment variable.

   ```bash
   host$ DISTRIBUTION=stable ./container up
   host$ DISTRIBUTION=stable ./container ssh
   ```

   ```bash
   host$ export DISTRIBUTION=stable
   host$ ./container up
   host$ ./container ssh
   ```

   2. Using the `--distribution` option for each command.

   ```bash
   host$ ./container up --distribution=stable
   host$ ./container ssh --distribution=stable
   ```

#### Using after Setup

After logging into the container, the source code is available in `/freedombox`
directory:

```bash
guest$ cd /freedombox
```

Run the development version of FreedomBox Service in the container using the
following command. This command continuously deploys your code changes into the
container providing a quick feedback cycle during development.

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

#### Troubleshooting

* Sometimes `host$ ./container destroy && ./container up` doesn't work. In such
  cases, try to delete the hidden `.container` folder and then `host$
  ./container up`.
* Not all kinds of changes are automatically updated. Try `guest$ sudo mount -o
  remount /freedombox`.
* I am getting an error that says `lo` is not managed by Network Manager
  * By default, Network Manager will not touch any interface mentioned in
    `/etc/network/interfaces`. <sup>[(src)][DebianNetworkManager]</sup>
    To workaround this error, you must override Network Manager's behavior.
    <sup>[(src)][GloballyManagedDevices]</sup>

    ```bash
    host$ sudo touch /etc/NetworkManager/conf.d/10-globally-managed-devices.conf
    host$ sudo service network-manager restart
    host$ ./container destroy && ./container up
    ```
* File/directory not found errors when running tests can be fixed by clearing `__pycache__` directories.

  ```bash
  host$ sudo find -iname '__pycache__' | sudo xargs rm -rf {} ;
  ```

#### Using Containers On 64-bit Raspberry Pi

The container script can be used (as described above) on a Raspberry Pi 3 or 4
running a 64-bit operating system.

If you are running Raspberry Pi OS 64-bit, you will first need to enable Network
Manager. To do this, run `sudo raspi-config`, go to "5 Advanced Options", and
then to "A4 Network Config". Select "NetworkManager", and then reboot as
prompted.

[back to index](#hacking)

[DebianNetworkManager]: https://wiki.debian.org/NetworkManager#Wired_Networks_are_Unmanaged
[GloballyManagedDevices]: https://askubuntu.com/a/893614

### Using Vagrant

Use VirtualBox and Vagrant if for some reason the container option is not
suitable, such as when you are running non-GNU/Linux machine or a non-systemd
machine.

#### For Debian GNU/Linux and Derivatives

1. Install Git, Vagrant and VirtualBox using apt.

   ```bash
   $ sudo apt install git virtualbox vagrant
   ```

##### Installing VirtualBox manually

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

#### For Other GNU/Linux Distributions or *BSDs

1. Install Git, Vagrant and VirtualBox using your favourite package manager.

#### For macOS (Intel CPUs)

1. Install [Homebrew](https://brew.sh/).

2. Install Git, VirtualBox and Vagrant using Homebrew.

   ```bash
   $ brew install git
   $ brew cask install virtualbox
   $ brew cask install vagrant
   ```

#### For macOS (Apple Silicon CPUs)

1. Install [Homebrew](https://brew.sh/) for macOS.

2. Install UTM (as an alternative to VirtualBox) for macOS.

    ```bash
    $ brew install --cask utm
    ```

Vagrant does not support UTM yet.

Apple's M1 and M2 chips should be powerful enough to virtualize/emulate an AMD64
Debian virtual machine. In this approach, we setup an entire development
environment in the virtual machine itself, not just the FreedomBox application.

##### Virtualization (fast)

You can install one of the pre-configured Debian images from the UTM gallery.
After downloading the zip file from the gallery, extract it to find a .utm file
that can be opened using UTM.

###### Emulation (slow)

Emulation allows you to run an AMD64 Debian image on UTM, but is significantly
slower and expensive on system resources.

1. [Download](https://www.debian.org/distrib/) a copy of the latest Debian
   distribution in ISO format.
2. Create a new virtual machine in UTM for FreedomBox development using the image.
   1. When creating the new VM, select "Emulate" and provide the path to the
      downloaded Debian image.
   2. Emulation will be very slow. Allocating 8 to 10 CPU cores and 8 to 12 GB of
      memory is recommended.
3. After installing Debian, shut down the machine and eject the image from the
   virtual CD-ROM drive.
4. The container script needs root priviliges to run. To give permissions to
   your user, run the following:

   ```bash
   $ su -
   # usermod -aG sudo <username>
   ```

**Tips**:
1. Refer to the [documentation](https://docs.getutm.app/guest-support/linux/)
   from UTM on how to enable clipboard sharing, dynamic screen resolution and
   shared folders.
2. Consider using Gnome Web as an alternative if Firefox runs into a crash loop
   inside the VM.

Once the Debian virtual machine is set up, the instructions to setup a
FreedomBox development environment inside it are the same as setting up on a
physical Debian machine (i.e. using a systemd-nspawn container).


#### For Windows

1. Install [Git](https://git-scm.com/download/windows),
   [VirtualBox](https://www.virtualbox.org/wiki/Downloads) and
   [Vagrant](https://www.vagrantup.com/downloads.html) from their respective
   download pages.

2. Tell Git to use Unix line endings by running the following in Git Bash.

   ```bash
   host$ git config --global core.autocrlf input
   ```

3. Run all the following commands inside Git Bash.

#### Setting Up Development Environment Using Vagrant

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

#### Using the Virtual Machine

After logging into the virtual machine (VM), the source code is available in
/freedombox directory:

```bash
vm$ cd /freedombox
```

Run the development version of FreedomBox Service (Plinth) from your source
directory in the virtual machine using the following command. This command
continuously deploys your code changes into the virtual machine providing a
quick feedback cycle during development.

```bash
vm$ freedombox-develop
```

If you have changed any system configuration files during your development,
you will need to run the following to install those files properly on to the
system and their changes to reflect properly.

```bash
vm$ sudo ./setup.py install
```

Note: This development virtual machine has automatic upgrades disabled by
default.


[back to index](#hacking)


## Making/keeping FreedomBox international

### Marking text for translation

To mark text for translation, FreedomBox uses Django's translation strings. A
module should e.g. `from django.utils.translation import gettext as _` and wrap
user-facing text with `_()`. Use it like this:

```python
message = _('Application successfully installed and configured.')
```

See [Django
documentation](https://docs.djangoproject.com/en/3.1/topics/i18n/translation/)
for more details.

### Translating literals (contributing translations)

The easiest way to start translating is with your browser, by using
[Weblate](https://hosted.weblate.org/projects/freedombox/plinth/).
Your changes will automatically get pushed to the code repository.

Alternatively, you can directly edit the `.po` file in your language directory
`Plinth/plinth/locale/` and create a pull request (see [CONTRIBUTING.md](CONTRIBUTING.md)).
In that case, consider introducing yourself on #freedombox IRC (irc.debian.org),
because some work may have been done already on the [Debian translators
discussion lists](https://www.debian.org/MailingLists/subscribe)
or the Weblate localization platform.

For more information on translations: https://wiki.debian.org/FreedomBox/Translate


[back to index](#hacking)


## Testing

### Running Tests

To run all the standard unit tests in the container/VM:

```bash
guest$ py.test-3
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

Some tests are skipped by default:
* tests that need root privileges,
* functional tests (they need additional preparation to run. See next section),
* tests that take much time to run.

Use `sudo` to run the ones that need root access:
```bash
guest$ sudo py.test-3
```

To force functional tests and tests that take long to run, set the environment
variable EXTENDED_TESTING=1:

```bash
guest$ EXTENDED_TESTING=1 py.test-3
```

To really run all tests, combine sudo with EXTENDED_TESTING:

```bash
guest$ sudo EXTENDED_TESTING=1 py.test-3
```

### Running the Test Coverage Analysis

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


[back to index](#hacking)


### Functional Tests

#### Install Dependencies

##### For running tests inside the container

Inside the container run

```bash
guest$ cd /freedombox ; sudo plinth/tests/functional/install.sh
```

##### For running tests inside the VM

From the host, provision the virtual machine with tests:

```bash
host$ vagrant provision --provision-with tests
```

##### For running tests on host machine

Follow the instructions below to run the tests on host machine. If you wish
perform the tests on host machine, the host machine must be based on Debian
Bookworm (or later).

```bash
host$ pip3 install --break-system-packages splinter
host$ pip3 install --break-system-packages pytest-splinter
host$ pip3 install --break-system-packages pytest-xdist  # optional, to run tests in parallel
host$ sudo apt install firefox
host$ sudo apt install smbclient  # optional, to test samba
```

- Install the latest version of
  [geckodriver](https://github.com/mozilla/geckodriver/releases). It is usually
  a single binary which you can place at `/usr/local/bin/geckodriver` .
  Geckodriver will use whichever binary is named 'firefox' for launching the
  browser and interacting with it.

#### Run FreedomBox Service

*Warning*: Functional tests will change the configuration of the system
 under test, including changing the hostname and users. Therefore you
 should run the tests using FreedomBox running on a throw-away VM.

The VM should have NAT port-forwarding enabled so that 4430 on the
host forwards to 443 on the guest. From where the tests are running, the web
interface of FreedomBox should be accessible at https://localhost:4430/.

To run samba tests, port 4450 on the host should be forwarded to port 445
on the guest.

#### Setup FreedomBox Service for tests

Via Plinth, create a new user as follows:

* Username: tester
* Password: testingtesting

This step is optional if a fresh install of Plinth is being tested. Functional
tests will create the required user using FreedomBox's first boot process.

#### Running Functional Tests

If you are testing a VM using NAT, and running the tests on the host,
then you need to specify the URL and ports:
```bash
host$ export FREEDOMBOX_URL=https://localhost:4430 FREEDOMBOX_SSH_PORT=2222 FREEDOMBOX_SAMBA_PORT=4450
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


[back to index](#hacking)


## Documentation

### Building the User Documentation Separately

FreedomBox Service (Plinth) man page is built from DocBook source in the `doc/`
directory. FreedomBox manual is downloaded from the wiki is also available
there. Both these are build during the installation process.

To build the documentation separately, run:

```bash
guest$ make -C doc
```

### Building Developer documentation

See [README.rst](doc/dev/README.rst) in `doc/dev` directory.


[back to index](#hacking)


## Submitting your changes

See [CONTRIBUTING.md](CONTRIBUTING.md) for information how to best contribute code.


[back to index](#hacking)


## Miscelanea

### Styling

FreedomBox uses Bootstrap as the CSS library for basic styling. However,
Bootstrap seems to encourage writing CSS within HTML by adding "utility"
classes. This is a bad practice that violates the separation of semantics from
presentation. It also leads to repetition of code that further leads to
inconsistencies. These utility classes must be used sparingly. Instead, CSS must
be written separately either for a specific page or for the entire interface
aiming for reuse.

### Application Icons

When adding a new App into FreedomBox, an icon is needed to represent the app in
the application view and for shortcuts in the front page. Follow these
guidelines for creating an app icon:

- Use SVG format.
- Keep the size and complexity of the SVG minimal. Simplify the graphic if
  necessary.
- Units for the entire document should be in pixels.
- View area should be 512x512 pixels.
- Background should be transparent.
- Leave no margins and prefer a square icon. If the icon is wide, leave top and
  bottom margins. If the icon is tall, leave left and right margins.

### Team Coordination

The project team coordinates by means of bi-weekly [audio
calls](https://wiki.debian.org/FreedomBox/ProgressCalls) and IRC discussions on
#freedombox-dev at oftc.net.

### Other Development Informations

* Generic [contribution overview](https://wiki.debian.org/FreedomBox/Contribute)
  * [How to create apps for FreedomBox (Developer Manual)](https://docs.freedombox.org)
  * User Experience [design](https://wiki.debian.org/FreedomBox/Design)
  * [Code contribution](https://wiki.debian.org/FreedomBox/Contribute/Code)


[back to index](#hacking)
