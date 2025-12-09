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
    vb.customize ["modifyvm", :id, "--firmware", "efi"]
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
    make provision-dev
  SHELL
  config.vm.provision "tests", run: "never", type: "shell", path: "plinth/tests/functional/install.sh"
  config.vm.post_up_message = "FreedomBox virtual machine is ready
for development. Plinth will be available at https://localhost:4430/plinth
(with an invalid SSL certificate). To watch logs:
$ vagrant ssh
$ sudo freedombox-logs
"

  config.trigger.after [:up, :resume, :reload] do |trigger|
    trigger.info = "Set plinth user permissions for development environment"
    trigger.run_remote = {
      path: ".vagrant-scripts/plinth-user-permissions.py"
    }
  end
  config.vm.boot_timeout=1200
end
