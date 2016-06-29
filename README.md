#Pluribus Networks - Ansible

#Ansible
 Ansible is an open source IT automation tool for configuration management, provisioning and application deployment. Ansible is agentless and does not require a software agent to be installed on the target nodes, it uses SSH for secured communication with the target nodes. The Pluribus Networks Ansible library provides support for using Ansible to deploy, configure and manage devices running Netvisor OS. This repository contains modules developed for Netvisor OS CLI to perform specific tasks on devices running Netvisor OS. These modules run CLI commands for installing Netvisor OS, configuring, retrieving information/device statistics, modifying configuration settings on the target nodes. 

#Getting started
 Ansible by default manages machines over the SSH protocol. Ansible is installed on a control machine that manages one or more nodes. Managed nodes do not require any agent software. 
 
##Control Machine Requirements 
  The Ansible control machine requires the following software:
  - SSH
  - Python 2.6 or later
  - Ansible 1.8 or later release 

##Managed Node Requirements
  The following software are requied on managed nodes:
  - SSH for communication
  - Python 2.6 or later

For a complete installation guide, please refer: [Ansible-Installation](https://docs.ansible.com/ansible/intro_installation.html)

#Modules
 Modules are library plugins that do the actual work. Modules get called and executed in playbook tasks. Modules are placed in ./library location. Modules return JSON format data. Documentation for each module can be accessed from the commandline using:
 ```
 ansible-doc <module> 
 ```
 
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
 
 - [pn_vlanshow.yml](ansible/examples/pn_vlanshow.yml)
 - [pn_vlanstatsshow.yml](ansible/examples/pn_vlanstatsshow.yml)
 - [pn_vlanstatssettingsshow.yml](ansible/examples/pn_vlanstatssettingsshow.yml)
 - [pn_vlancreate.yml](ansible/examples/pn_vlancreate.yml)
 - [pn_vlandelete.yml](ansible/examples/pn_vlandelete.yml)
 - [pn_vlagcreate.yml](ansible/examples/pn_vlagcreate.yml)
 - [pn_vlagdelete.yml](ansible/examples/pn_vlagdelete.yml)
 - [pn_clustercreate.yml](ansible/examples/pn_clustecreate.yml)
 - [pn_clusterdelete.yml](ansible/examples/pn_clusterdelete.yml)

[YAML Lint](http://www.yamllint.com/) (online) helps you debug YAML syntax if you are having problems
 
#Inventory
 Ansible can work against multiple nodes in the infrastructure simultaneously. This is done by selecting a group of nodes in the Ansible's inventory file located at /etc/ansible/hosts on the control machine. This file (see [hosts](ansible/hosts))is configurable. Please refer: [Ansible-Inventory](https://docs.ansible.com/ansible/intro_inventory.html) for more on this.

