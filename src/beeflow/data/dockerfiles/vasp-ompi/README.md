**Note**: If this is difficult to read, use your browser's *Zoom In* (&#8984;+) 
and *Zoom Out* (&#8984;-) feature to change the text size.

## Building a VASP Container Using Vagrant

You'll need to make some allowances for LANL proxies when using Vagrant on LANL
systems. First, load the `vagrant-proxyconf` plugin (you only need to do this
once):

```sh
> vagrant plugin install vagrant-proxyconf
> vagrant plugin list
vagrant-proxyconf (2.0.0, global)
```

Now add the following `Vagrantfile` to `~/.vagrant.d`. This file gets executed
every time you run `vagrant` and inserts proxies where necessary.

```ruby
# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  puts "proxyconf..."
  if Vagrant.has_plugin?("vagrant-proxyconf")
    puts "found proxyconf plugin !"
    if ENV["http_proxy"]
      puts "http_proxy: " + ENV["http_proxy"]
      config.proxy.http = ENV["http_proxy"]
    end
    if ENV["https_proxy"]
      puts "https_proxy: " + ENV["https_proxy"]
      config.proxy.https = ENV["https_proxy"]
    end
    if ENV["no_proxy"]
      puts "no_proxy: " + ENV["no_proxy"]
      config.proxy.no_proxy = ENV["no_proxy"]
    end
  end
end
```
                            
Place the following `Vagrantfile` in the project directory:

```ruby
# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "ubuntu/xenial64"
  # prevent log file on host
  config.vm.provider "virtualbox" do |vb|
    vb.customize ["modifyvm", :id, "--uartmode1", "disconnected"]
  end
  config.vm.provision :docker
end
```

Now start the VM (download the image if necessary) and ssh in to the running VM:

```sh
> vagrant up
...lots of stuff printed...
> vagrant ssh
vagrant@ubuntu-xenial:~$ which docker
/usr/bin/docker
```

You still need to tell the Docker daemon about LANL proxies before it will work
properly. There are likely other ways to do this (like setting proxy variables
on `docker` command lines), but this seems easiest for LANL systems.

In the Vagrant VM (which you got to via `vagrant ssh`):

```sh
vagrant@ubuntu-xenial:~$ sudo mkdir -p /etc/systemd/system/docker.service.d
vagrant@ubuntu-xenial:~$ sudo touch /etc/systemd/system/docker.service.d/http-proxy.conf
```

Now edit that file and add:

```
[Service]
Environment="HTTP_PROXY=http://proxyout.lanl.gov:8080/" "NO_PROXY=localhost,127.0.0.1,.lanl.gov"
```

Now you need to restart the Docker daemon so that it recognizes these changes:

```sh
vagrant@ubuntu-xenial:~$ sudo systemctl daemon-reload
vagrant@ubuntu-xenial:~$ sudo systemctl restart docker
vagrant@ubuntu-xenial:~$ systemctl show --property=Environment docker
Environment=HTTP_PROXY=http://proxyout.lanl.gov:8080/NO_PROXY=localhost,127.0.0.1,.lanl.gov
q (need to type this to get out of display mode)
```

Now you should be able to run Docker:

```sh
vagrant@ubuntu-xenial:~$ docker run hello-world
Hello from Docker!
This message shows that your installation appears to be working correctly.
...
```


