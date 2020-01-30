# -*- mode: ruby -*-
# vi: set ft=ruby :
#
# This file is part of FreedomBox.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
Vagrant.configure(2) do |config|
  config.vm.box = "freedombox/plinth-dev"
  config.vm.network "forwarded_port", guest: 443, host: 4430
  config.vm.network "forwarded_port", guest: 445, host: 4450
  config.vm.synced_folder ".", "/vagrant", owner: "plinth", group: "plinth"
  config.vm.provider "virtualbox" do |vb|
    vb.cpus = 2
    vb.memory = 2048
    vb.linked_clone = true
  end
  config.vm.provision "shell", run: 'always', inline: <<-SHELL
    # Disable automatic upgrades
    /vagrant/actions/upgrades disable-auto
    # Do not run system plinth
    systemctl stop plinth
    systemctl disable plinth
  SHELL
  config.vm.provision "shell", inline: <<-SHELL
    cd /vagrant/
    ./setup.py install
    systemctl daemon-reload
    # Stop any ongoing upgrade
    killall -9 unattended-upgr
    dpkg --configure -a
    apt -f install
    apt-get update
    # In case new dependencies conflict with old dependencies
    apt-mark hold freedombox
    DEBIAN_FRONTEND=noninteractive apt-get install -y $(plinth --list-dependencies)
    apt-mark unhold freedombox
    # Install ncurses-term
    DEBIAN_FRONTEND=noninteractive apt-get install -y ncurses-term
  SHELL
  config.vm.provision "tests", run: "never", type: "shell", path: "functional_tests/install.sh"
  config.vm.post_up_message = "FreedomBox virtual machine is ready
for development. You can run the development version of Plinth using
the following command.
$ vagrant ssh
$ sudo -u plinth /vagrant/run --develop
Plinth will be available at https://localhost:4430/plinth (with
an invalid SSL certificate).
"

  config.trigger.after [:up, :resume, :reload] do |trigger|
    trigger.info = "Set plinth user permissions for development environment"
    trigger.run_remote = {
      path: "vagrant-scripts/plinth-user-permissions.py"
    }
  end
  config.trigger.before :destroy do |trigger|
    trigger.warn = "Performing cleanup steps"
    trigger.run = {
      path: "vagrant-scripts/post-box-destroy.py"
    }
  end
  config.vm.boot_timeout=1200
end
