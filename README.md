#Pluribus Networks - Ansible
 
# Index
  + [Ansible](#ansible)
  + [Getting Started](#getting-started)
    - [Installation](#installation)
    - [Control Machine Requirements](#control-machine-requirements)
    - [Managed Node Requirements](#managed-node-requirements)
  + [Pluribus Ansible Modules](#pluribus-ansible-modules)
  + [Inventory](#inventory)
  + [Configuration File](#configuration-file)
  + [Modules](#modules)
  + [Playbooks](#playbooks)

#Ansible
 Ansible is an open source IT automation tool for configuration management, provisioning and application deployment. Ansible is agentless and does not require a software agent to be installed on the target nodes. It uses SSH for secured communication with the target nodes. The Pluribus Networks Ansible library provides support for using Ansible to deploy, configure and manage devices running Netvisor OS. This repository contains modules developed for Netvisor OS CLI to perform specific tasks on devices running Netvisor OS. These modules run CLI commands for installing Netvisor OS, configuring, retrieving information/device statistics, modifying configuration settings on the target nodes. 

#Getting Started

##Installation
 Ansible by default manages machines over the SSH protocol. Ansible is installed on a control machine that manages one or more nodes. Managed nodes do not require any agent software. 

##Control Machine Requirements 
 The host you want to use as the control machine requires Python 2.6 or later. This control machine can be a desktop/laptop/workstation running a Linux based OS or any version of BSD. 
 The Ansible control machine requires the following software:
 
 * SSH
 * Python 2.6 or later
 * Ansible 1.8 or later release
   
 The steps for installing Ansible on Debian/Ubuntu is outlined here. 
 To get the latest version of Ansible:
```
  $ sudo apt-add-repository ppa:ansible/ansible -y                     
  $ sudo apt-get update && sudo apt-get install ansible -y
```
 To install Ansible on other platforms, please refer: [Ansible-Installation](https://docs.ansible.com/ansible/intro_installation.html)

##Managed Node Requirements
 Communication with managed nodes is over SSH. By default it uses sftp, but you can switch to scp in ansible.cfg
 As with the control machine, the managed nodes require Python 2.6 or later. (For nodes running Python 2.5 or lesser version, you may need python-simplejson)
 
##Pluribus ansible modules
 Pluribus ansible modules are not included in the core Ansible code base. You will have to clone this repository in your local machine to use Pluribus ansible modules. 
 
 To use pluribus-ansible modules or develop modules for pluribus-ansible, clone this repository in the path where you installed ansible. You can have it in a different project directory but make sure you modify the ansible.cfg file with relevant paths. 

```
~$ cd /etc/ansible
~:/etc/ansible$ git clone <url>
~:/etc/ansible$ cd pluribus-ansible
~:/etc/ansible/pluribus-ansible$ git checkout -b <your branch>
```

Now you can begin working on your branch.

#NOTE: 
Checklist:
  1. Make sure you set the library path to point to your library directory in the `ansible.cfg` file.
  2. Disable host key checking in `ansible.cfg` file. If required, establish SSH keys.
  3. Make other configuration changes as required.

#Inventory
 Ansible can work against multiple nodes in the infrastructure simultaneously. This is done by selecting a group of nodes in the Ansible's inventory file which is by default saved at /etc/ansible/hosts on the control machine. This file (see [hosts](ansible/hosts))is configurable.
```
 mail.example.com

 [webservers]
 foo.example.com
 bar.example.com

 [dbservers]
 serverone.example.com
 servertwo.example.com
 serverthree.example.com
``` 
 Group names are enclosed in brackets and are used to classify systems based on purpose. 
 A node can be a part of multiple groups or none.
 Please refer: [Ansible-Inventory](https://docs.ansible.com/ansible/intro_inventory.html) for more on this.

#Configuration File
 The ansible.cfg file is used to configure certain settings in ansible. The default settings should be sufficient for most of the purposes.
 
 If you installed ansible from a package manager, the ansible.cfg will be present in /etc/ansible directory. 
 If you installed ansible from pip or other source or if its not present, you can create one to override default settings.
 Please refer: [Ansible-Configuration](http://docs.ansible.com/ansible/intro_configuration.html) for more on this.

#Modules
 Ansible modules reusable, standalone scripts that do the actual work. Modules get called and executed in playbook tasks.
 Modules return information to ansible in JSON format. Modules can be placed in different places where ansible looks for modules. As a convenience, we place them under library directory in our ansible project directory.
 
 Pluribus Networks CLI modules:
 
 - [pn_show](ansible/library/pn_show.py): To execute CLI show commands
 - [pn_vlan](ansible/library/pn_vlan.py): To create/delete/modify VLANs
 - [pn_vlag](ansible/library/pn_vlag.py): To create/delete/modify VLAGs
 - [pn_cluster](ansible/library/pn_cluster.py): To create/delete/modify Clusters
 - [pn_trunk](ansible/library/pn_trunk.py): To create/delete/modify Trunks(LAGs)
 - [pn_vrouter](ansible/library/pn_vrouter.py): To create/delete/modify vRouters


#Playbooks
 Playbooks are Ansible's configuration, deployment and orchestration language. Playbooks are expressed in [YAML](https://docs.ansible.com/ansible/YAMLSyntax.html) format and have a minimum of syntax. Each playbook is composed of one or more plays. The goal of a play is to map a group of hosts to some well defined tasks. A task is basically a call to an Ansible Module. 
 
 Some example playbooks:
 
 - [pn_vlanshow.yml](ansible/roles/examples/pn_vlanshow.yml)
 - [pn_vlanstatsshow.yml](ansible/roles/examples/pn_vlanstatsshow.yml)
 - [pn_vlanstatssettingsshow.yml](ansible/roles/examples/pn_vlanstatssettingsshow.yml)
 - [pn_vlancreate.yml](ansible/roles/examples/pn_vlancreate.yml)
 - [pn_vlandelete.yml](ansible/roles/examples/pn_vlandelete.yml)
 - [pn_vlagcreate.yml](ansible/roles/examples/pn_vlagcreate.yml)
 - [pn_vlagdelete.yml](ansible/roles/examples/pn_vlagdelete.yml)
 - [pn_clustercreate.yml](ansible/roles/examples/pn_clustecreate.yml)
 - [pn_clusterdelete.yml](ansible/roles/examples/pn_clusterdelete.yml)

[YAML Lint](http://www.yamllint.com/) (online) helps you debug YAML syntax.
 

