# Install Dependencies

```
$ sudo apt install python3-pytest
$ pip3 install splinter
$ pip3 install pytest-splinter
$ pip3 install pytest-bdd
$ sudo apt install xvfb  # optional, to avoid opening browser windows
$ pip3 install pytest-xvfb  # optional, to avoid opening browser windows
```

- Install the latest version of geckodriver. 
It's usually a single binary which you can place at /usr/local/bin/geckodriver

- Install the latest version of Mozilla Firefox. 
Download and extract the latest version from the Firefox website and symlink the binary named `firefox` to /usr/local/bin.

Geckodriver will then use whatever version of Firefox you symlink as /usr/local/bin/firefox.

# Run FreedomBox Service

*Warning*: Functional tests will change the configuration of the system
 under test, including changing the hostname and users. Therefore you
 should run the tests using FreedomBox running on a throw-away VM.

The VM should have NAT port-forwarding enabled so that 4430 on the
host forwards to 443 on the guest. The web interface of FreedomBox 
should be accessible from the host system at https://localhost:4430/.

# Setup FreedomBox Service for tests

Create a new user as follows:

* Username: tester
* Password: testingtesting

This step is optional if a fresh install of Plinth is being
tested. Functional tests will create the required user using FreedomBox's
first boot process.

# Run Functional Tests

From the directory functional_tests, run

```
$ py.test
```

The full test suite can take a long time to run (over 15 minutes). You
can also specify which tests to run, by tag or keyword:

```
$ py.test -k essential
```

If xvfb is installed and you still want to see browser windows, use the 
`--no-xvfb` command-line argument.

```
$ py.test --no-xvfb -k mediawiki
```
