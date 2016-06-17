# pluribus-ansible

##Ansible
Ansible is an IT automation platform for configuration, management and orchestration of systems and applications. 
Pluribus Networks provides support for using Ansible to deploy, configure and manage devices running Netvisor Operating System.

#Requirements:
 - SSH
 - Python 2.6 and above
 - Ansible(1.8 and above) on the control machine

#Modules:
 - [pn_show](ansible/library/pn_show.py): To execute CLI show commands
 - [pn_vlan](ansible/library/pn_vlan.py): To create/delete vlans
 - [pn_vlag](ansible/library/pn_vlag.py): To create/delete vlags
 - [pn_clustercreate](ansible/library/pn_clustercreate.py): To create clusters
 - [pn_clusterdelete](ansible/library/pn_clusterdelete.py): To delete clusters

#Sample Playbooks:

 - [pn_vlan_show.yml](ansible/examples/pn_vlan_show.yml)
 - [pn_vlan_stats_show.yml](ansible/examples/pn_vlan_stats_show.yml)
 - [pn_vlan_stats_settings_show.yml](ansible/examples/pn_vlan_stats_settings_show.yml)
 - [pn_vlancreate.yml](ansible/examples/pn_vlancreate.yml)
 - [pn_vlandelete.yml](ansible/examples/pn_vlandelete.yml)
 - [pn_vlagcreate.yml](ansible/examples/pn_vlagcreate.yml)
 - [pn_vlagdelete.yml](ansible/examples/pn_vlagdelete.yml)
 - [pn_clustercreate.yml](ansible/examples/pn_clustecreate.yml)
 - [pn_clusterdelete.yml](ansible/examples/pn_clusterdelete.yml)

#Inventory file path: 
 - /etc/ansible/hosts

#Syntax 
 - command: ansible-playbook /etc/ansible/pn_vlan_show.yml -i /etc/ansible/hosts -k
