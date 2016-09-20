# -*- mode: ruby -*-
# vi: set ft=ruby :
#
# This file is part of Plinth.
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
    systemctl daemon-reload
    systemctl restart plinth
  SHELL
  config.vm.post_up_message = "FreedomBox machine is ready for Plinth development.
You can access it on https://localhost:4430/plinth/ (with an invalid
SSL certificate). You can modify source code on the host machine and
then test it by running:
$ vagrant provision
"
end
