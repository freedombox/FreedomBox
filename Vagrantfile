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
  config.vm.provision "shell", inline: <<-SHELL
    cd /vagrant/
    ./setup.py install
    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get install -y $(plinth --list-dependencies)
    systemctl daemon-reload
  SHELL
  config.vm.provision "shell", run: 'always', inline: <<-SHELL
    # Do not run system plinth
    systemctl stop plinth
    systemctl disable plinth
    # Disable automatic upgrades
    /vagrant/actions/upgrades disable-auto
    # Install ncurses-term
    DEBIAN_FRONTEND=noninteractive apt-get install -y ncurses-term
  SHELL
  config.vm.post_up_message = "FreedomBox virtual machine is ready
for development. You can run the development version of Plinth using
the following command.
$ vagrant ssh
$ sudo /vagrant/run --develop
Plinth will be available at https://localhost:4430/plinth (with
an invalid SSL certificate).
"
end
