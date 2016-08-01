# -*- mode: ruby -*-
# vi: set ft=ruby :
Vagrant.configure(2) do |config|
  config.vm.box = "jvalleroy/plinth-dev"
  config.vm.network "forwarded_port", guest: 443, host: 4430
  config.vm.provision "shell", inline: <<-SHELL
    cp -R /vagrant /home/vagrant/plinth
    cd /home/vagrant/plinth
    python3 setup.py install
    systemctl daemon-reload
    systemctl restart plinth
  SHELL
end
