# pluribus-ansible

##Ansible
Ansible is an IT automation platform for configuration, management and orchestration of systems and applications. 
Pluribus Networks provides support for using Ansible to deploy, configure and manage devices running on Netvisor Operating System.

#Requirements:
 - SSH
 - Python 2.6 and above
 - Ansible(1.8 and above) on the control machine

#Modules:
 - pn_show: To execute CLI show commands
 - pn_vlan: To create/delete vlans
 - pn_vlag: To create/delete vlags
 - pn_clustercreate: To create clusters
 - pn_clusterdelete: To delete clusters

#Sample Playbooks:

 - pn_vlan_show.yml
 - pn_vlan_stats_show.yml
 - pn_vlan_stats_settings_show.yml
 - pn_vlancreate.yml
 - pn_vlandelete.yml
 - pn_vlagcreate.yml
 - pn_vlagdelete.yml
 - pn_clustecreate.yml
 - pn_clusterdelete.yml

#Inventory file path: 
 - /etc/ansible/hosts

#Syntax 
 - command: ansible-playbook /etc/ansible/pn_vlan_show.yml -i /etc/ansible/hosts -k
