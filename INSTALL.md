# Installing FreedomBox Service (Plinth)

The following instructions are for installing FreedomBox from source code meant
for advanced users. For regular use of FreedomBox, instructions are available on
FreedomBox [Manual](https://wiki.debian.org/FreedomBox/Manual/)'s
[QuickStart](https://wiki.debian.org/FreedomBox/Manual/QuickStart) page.

1. Install FreedomBox Service (Plinth):

    A Debian based system is needed to run FreedomBox. Buster release or later
    is recommended. Unzip the source into a directory. Change to the directory
    containing the program and run:

    ```
    $ sudo apt build-dep .
    ```

    ```
    $ sudo apt install -y $(./run --develop --list-dependencies)
    ```

    Install additional dependencies by picking the list from debian/control file
    fields Depends: and Recommends: for the package ''freedombox''. After that
    install FreedomBox Service (Plinth) itself.

    ```
    $ sudo make build install
    ```

2.  Run FreedomBox Service (Plinth):

    ```
    $ sudo plinth
    ```

3.  Access FreedomBox UI:

    UI should be accessible at http://localhost:8000/plinth

If you are installing FreedomBox Service (Plinth) for development purposes, see
HACKING.md instead.
