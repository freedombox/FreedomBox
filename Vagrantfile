# -*- mode: ruby -*-
# vi: set ft=ruby :
# SPDX-License-Identifier: AGPL-3.0-or-later

require 'etc'

Vagrant.configure(2) do |config|
  config.vm.box = "freedombox/freedombox-testing-dev"
  config.vm.network "forwarded_port", guest: 443, host: 4430
  config.vm.network "forwarded_port", guest: 445, host: 4450
  config.vm.synced_folder ".", "/freedombox", owner: "plinth", group: "plinth"
  config.vm.provider "virtualbox" do |vb|
    vb.cpus = Etc.nprocessors
    vb.memory = 2048
    vb.linked_clone = true
  end
  config.vm.provision "shell", run: 'always', inline: <<-SHELL
    # Disable automatic upgrades
    echo -e 'APT::Periodic::Update-Package-Lists "0";\nAPT::Periodic::Unattended-Upgrade "0";' > //etc/apt/apt.conf.d/20auto-upgrades
    # Do not run system plinth
    systemctl stop plinth
    systemctl disable plinth
  SHELL
  config.vm.provision "shell", inline: <<-SHELL
    cd /freedombox/
    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get build-dep --no-install-recommends --yes .
    make build install
    systemctl daemon-reload
    # Stop any ongoing upgrade
    killall -9 unattended-upgr
    dpkg --configure -a
    apt -f install
    apt-get update
    # In case new dependencies conflict with old dependencies
    apt-mark hold freedombox
    DEBIAN_FRONTEND=noninteractive apt-get install --no-upgrade -y $(sudo -u plinth ./run --develop --list-dependencies)
    apt-mark unhold freedombox
    # Install ncurses-term
    DEBIAN_FRONTEND=noninteractive apt-get install -y ncurses-term
    echo 'alias freedombox-develop="cd /freedombox; sudo -u plinth /freedombox/run --develop"' >> /home/vagrant/.bashrc
  SHELL
  config.vm.provision "tests", run: "never", type: "shell", path: "plinth/tests/functional/install.sh"
  config.vm.post_up_message = "FreedomBox virtual machine is ready
for development. You can run the development version of Plinth using
the following command.
$ vagrant ssh
$ freedombox-develop
Plinth will be available at https://localhost:4430/plinth (with
an invalid SSL certificate).
"

  config.trigger.after [:up, :resume, :reload] do |trigger|
    trigger.info = "Set plinth user permissions for development environment"
    trigger.run_remote = {
      path: ".vagrant-scripts/plinth-user-permissions.py"
    }
  end
  config.vm.boot_timeout=1200
end
