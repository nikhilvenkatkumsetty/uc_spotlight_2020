# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure('2') do |config|

  config.vm.box      = 'centos/7'
  config.vm.hostname = 'webhooks.esri.com'
  config.vm.network :public_network

  config.vm.provider 'virtualbox' do |vb|
    vb.memory = '4096'
    vb.name   = 'webhooks'
  end

  config.vm.provision 'shell', path: 'provision.sh'
  
end
