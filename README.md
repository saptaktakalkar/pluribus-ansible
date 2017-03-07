#Pluribus Networks - Ansible
 
# Index
  + [Ansible](#ansible)
  + [Getting Started](#getting-started)
    - [Installation](#installation)
    - [Control Machine Requirements](#control-machine-requirements)
    - [Managed Node Requirements](#managed-node-requirements)
  + [Inventory](#inventory)
  + [Configuration File](#configuration-file)
  + [Modules](#modules)
  + [Playbooks](#playbooks)
  + [Security](#security)

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
 

#Inventory
 Ansible can work against multiple nodes in the infrastructure simultaneously. This is done by selecting a group of nodes in the Ansible's inventory file which is by default saved at /etc/ansible/hosts on the control machine. This file (see [hosts](hosts.sample))is configurable.
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
 Custom changes to the ansible workflow and how it behaves are made through the configuration file. If you installed ansible from a package manager, the `ansible.cfg` will be present in `/etc/ansible` directory. If it is not present, you can create one to override default settings. Although the default settings should be sufficient for most of the purposes, you may need to change some of the settings based on your requirements.
  The default configuration file can be found here: [ansible.cfg](ansible.cfg.sample)

#Modules
 Ansible modules reusable, standalone scripts that do the actual work. Modules get called and executed in playbook tasks.
 Modules return information to ansible in JSON format. Modules can be placed in different places where ansible looks for modules. As a convenience, we place them under library folder in our ansible project directory.
 
 **Pluribus Ansible Modules**
   Pluribus Ansible modules support following configurations. These modules are idempotent. More information about these modules, options and their usage can be found in [Modules](module_docs). 
 
 - [pn_initial_ztp](ansible/library/pn_initial_ztp.py): To create/join fabric during zero touch provisioning.
 - [pn_l2_ztp](ansible/library/pn_l2_ztp.py): To auto configure vlags for layer2 fabric.
 - [pn_l3_ztp](ansible/library/pn_l3_ztp.py): To auto configure link IPs for layer3 fabric.
 - [pn_ztp_vrrp_l2](ansible/library/pn_ztp_vrrp_l2_csv.py): To configure VRRP (Virtual Router Redundancy Protocol) for layer2 fabric.
 - [pn_ztp_vrrp_l3](ansible/library/pn_ztp_vrrp_l3.py): To configure VRRP (Virtual Router Redundancy Protocol) for layer3 fabric.
 - [pn_ebgp_ospf](ansible/library/pn_ebgp_ospf.py): To configure eBGP/OSPF.
 - [pn_vflow](ansible/library/pn_flow.py): To create/delete/modify vFlows.
 - [pn_vxlan](ansible/library/pn_vxlan.py): To configure vxlan.
 - [pn_l1_mode](ansible/library/pn_l1_mode.py): To create link association between two switches which are not connected to each other.
 - [pn_switch_config_reset](ansible/library/pn_switch_config_reset.py): To reset the switch configuration to factory default.
 - [pn_show](ansible/library/pn_show.py): To execute CLI show commands.
 - [pn_vlan](ansible/library/pn_vlan.py): To create/delete/modify VLANs.
 - [pn_vlag](ansible/library/pn_vlag.py): To create/delete/modify VLAGs.
 - [pn_cluster](ansible/library/pn_cluster.py): To create/delete Clusters.
 - [pn_trunk](ansible/library/pn_trunk.py): To create/delete/modify Trunks(LAGs).
 - [pn_vrouter](ansible/library/pn_vrouter.py): To create/delete/modify vRouters.
 - [pn_vrouterif](ansible/library/pn_vrouterif.py): To add/remove vRouter interfaces(including VRRP).
 - [pn_vrouterlbif](ansible/library/pn_vrouterlbif.py): To add/remove vRouter Loopback interfaces.
 - [pn_vrouterbgp](ansible/library/pn_vrouterbgp.py): To add/remove vRouter BGP configurations.
 - [pn_ospf](ansible/library/pn_ospf.py): To add/remove vRouter OSPF configurations.

 
 Pluribus ansible modules are not included in the core Ansible code base. You will have to clone this repository in your local machine to use Pluribus ansible modules. 
 To use pluribus-ansible modules or develop modules for pluribus-ansible, clone this repository in the path where you installed ansible. You can have it in a different project directory but make sure you modify the ansible.cfg file with relevant paths. 

```
~$ mkdir <directory-name>
~$ cd <directory-name>
~:<directory-name>$ git clone <url>
~:<directory-name>$ cd pluribus-ansible
~:<directory-name>/pluribus-ansible$ git checkout -b <your branch>
```

Now you can begin working on your branch.

**NOTE**: 
Checklist:
  1. Make sure you set the library path to point to your library directory in the `ansible.cfg` file.
  2. Disable host key checking in `ansible.cfg` file. If required, establish SSH keys.
  3. Make other configuration changes as required.
 

#Playbooks
 Playbooks are Ansible's configuration, deployment and orchestration language. Playbooks are expressed in [YAML](https://docs.ansible.com/ansible/YAMLSyntax.html) format and have a minimum of syntax. Each playbook is composed of one or more plays. The goal of a play is to map a group of hosts to some well defined tasks. A task is basically a call to an Ansible Module. 
 
 Some example playbooks:
 
 - [pn_initial_ztp.yml](ansible/playbooks/pn_initial_ztp.yml)
 - [pn_l2_ztp.yml](ansible/playbooks/pn_l2_ztp.yml)
 - [pn_l3_ztp.yml](ansible/playbooks/pn_l3_ztp.yml)
 - [pn_vrrp_l2_with_csv.yml](ansible/playbooks/pn_vrrp_l2_with_csv.yml)
 - [pn_l3_vrrp_ebgp.yml](ansible/playbooks/pn_l3_vrrp_ebgp.yml)
 - [pn_l3_vrrp_ospf.yml](ansible/playbooks/pn_l3_vrrp_ospf.yml)
 - [pn_vflow_create.yml](ansible/playbooks/pn_vflow_create.yml)
 - [pn_vflow_delete.yml](ansible/playbooks/pn_vflow_delete.yml)
 - [pn_vxlan.yml](ansible/playbooks/pn_vxlan.yml)
 - [pn_switch_reset.yml](ansible/playbooks/pn_switch_reset.yml)
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
 
 
#Security
 Netvisor CLI has a one stage authentication process requiring login credentials to use CLI on devices running ONVL. These credentials have to be passed to the Pluribus Ansible modules through playbooks via the parameters `pn_cliusername` and `pn_clipassword`. However it is not a best practice to provide plain-text login credentials for security concerns. These login credentials are not required if root login is enabled on target nodes but this is not recommended unless you have a good reason.
 Ansible Vault to the rescue!
   Ansible vault is a feature of ansible that allows keeping sensitive data such as passwords or keys in encrypted files rather than as plain-text in your playbooks or roles. 
   To enable this feature, a command line tool, `ansible-vault` is used to edit files and a command line flag `--ask-vault-pass` is used. If you have different credentials for different devices, you can encrypt them in `group_vars/` or `host_vars/` inventory variables,  variables loaded by `include_vars` or `vars_files`. 
   Please refer: [Ansible-Vault](http://docs.ansible.com/ansible/playbooks_vault.html) for more on this.
   
 **Creating Encrypted Files**
   To create a new encrypted data file, run the following command:
```
ansible-vault create foo.yml
```

  First you will be prompted for a password.
  After providing a password, the tool will launch an editor(defaults to vi). Here you can enter the sensitive data.

```
USERNAME: admin
PASSWORD: admin
```

  Once you have created the file, it will be saved as encrypted data. The default cipher is AES.
  
  The playbook will look like:
```
---
- name: vlan show using Vault encrypted file
  hosts: spine[0]
  user: pluribus
  
  vars_files:
  - foo.yml
  
  tasks:
  - name: Run vlan-show command
    pn_show: 
      pn_cliusername:{{ USERNAME }} 
      pn_clipassword={{ PASSWORD }} 
      pn_command=vlan-show
    register: show_output

  - debug: var=show_output
```
  
 **Running a Playbook with Vault**
   To run the play book, include the `--ask-vault-pass` flag in the command line.
```
ansible-playbook playbook.yml --ask-vault-pass
```
  

