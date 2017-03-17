# Pluribus Networks - Ansible
 
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
  + [Setup Key Based Authentication](#setup-key-based-authentication)
  + [Running Playbooks](#running-playbooks)
  + [Troubleshooting Utilities!](#troubleshooting-utilities)
  
# Ansible
 Ansible is an open source IT automation tool for configuration management, provisioning and application deployment. Ansible is agentless and does not require a software agent to be installed on the target nodes. It uses SSH for secured communication with the target nodes. The Pluribus Networks Ansible library provides support for using Ansible to deploy, configure and manage devices running Netvisor OS. This repository contains modules developed for Netvisor OS CLI to perform specific tasks on devices running Netvisor OS. These modules run CLI commands for installing Netvisor OS, configuring, retrieving information/device statistics, modifying configuration settings on the target nodes. 

# Getting Started

## Installation
 Ansible by default manages machines over the SSH protocol. Ansible is installed on a control machine that manages one or more nodes. Managed nodes do not require any agent software. 

## Control Machine Requirements 
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

## Managed Node Requirements
 Communication with managed nodes is over SSH. By default it uses sftp, but you can switch to scp in ansible.cfg
 As with the control machine, the managed nodes require Python 2.6 or later. (For nodes running Python 2.5 or lesser version, you may need python-simplejson)
 

# Inventory
 Ansible can work against multiple nodes in the infrastructure simultaneously. This is done by selecting a group of nodes in the Ansible's inventory file which is by default saved at /etc/ansible/hosts on the control machine. This file (see the default [hosts](hosts.sample) file)is configurable.
 
```
aquarius.pluribusnetworks.com
 
[spine]
gui-spine1 ansible_host=10.9.21.60 ansible_user="{{ SSH_USER }}" ansible_ssh_pass="{{ SSH_PASS }}" ansible_become_pass="{{ SSH_PASS }}"
gui-spine2 ansible_host=10.9.21.61 ansible_user="{{ SSH_USER }}" ansible_ssh_pass="{{ SSH_PASS }}" ansible_become_pass="{{ SSH_PASS }}"

[leaf]
gui-leaf1 ansible_host=10.9.21.62 ansible_user="{{ SSH_USER }}" ansible_ssh_pass="{{ SSH_PASS }}" ansible_become_pass="{{ SSH_PASS }}"
gui-leaf2 ansible_host=10.9.21.63 ansible_user="{{ SSH_USER }}" ansible_ssh_pass="{{ SSH_PASS }}" ansible_become_pass="{{ SSH_PASS }}"
gui-leaf3 ansible_host=10.9.21.64 ansible_user="{{ SSH_USER }}" ansible_ssh_pass="{{ SSH_PASS }}" ansible_become_pass="{{ SSH_PASS }}"
gui-leaf4 ansible_host=10.9.21.65 ansible_user="{{ SSH_USER }}" ansible_ssh_pass="{{ SSH_PASS }}" ansible_become_pass="{{ SSH_PASS }}"

[cisco-spine]
nexus9k-spine.pluribusnetworks.com

[arista-spine]
aristaeOs-spine.pluribusnetworks.com

[juniper-spine]
junos-spine.pluribusnetworks.com

[wan]
pn_wan

``` 

 Group names are enclosed in brackets and are used to classify systems based on purpose. 
 A node can be a part of multiple groups or none.
 Ansible allows us to specify corresponding host-dependent parameters in the hosts file itself. These variables can be used in the playbooks by enclsing them with flower brackets`{{ variable_name }}`. Some of these include:
 - **ansible_host** : Specify the name or IP address of the host to connect to.
 - **ansible_port** : Specify the non-standard SSH port if you're not using the default port 22.
 - **ansible_user** : Specify the SSH username to use.
 - **ansible_ssh_pass** : \*Specify the SSH password to use.
 - **ansible_become_pass** : \*Specify the privilage escalation password(sudo/su).
 - **ansible_ssh_private_key_file** : \*Specify the private key file used for password less SSH.
 
 \*Please note that these varaibles should not be stored as plain-text! You can store them in an AES encrypted vault file and access them as shown above. Lookup [Security](#security) for more on this.
 
 Please refer: [Ansible-Inventory](https://docs.ansible.com/ansible/intro_inventory.html) for more information on how to configure the hosts file.


# Configuration File
  Custom changes to the ansible workflow and how it behaves are made through the configuration file. If you installed ansible from a package manager, the `ansible.cfg` will be present in `/etc/ansible` directory. If it is not present, you can create one to override default settings. Although the default settings should be sufficient for most of the purposes, you may need to change some of the settings based on your requirements.
  The default configuration file can be found here: [ansible.cfg](ansible.cfg.sample)

**Checklist**:
  1. Make sure you set the library path to point to your library directory in the `ansible.cfg` file.
  2. Disable host key checking in `ansible.cfg` file. If required, establish SSH keys(Use [pn_autossh](/ansible/library/pn_autossh.py) module to easily setup SSH keys!).
  3. Make other configuration changes as required.

 Snapshot of example config file:

```
*** snippet ***
#inventory      = /etc/ansible/hosts
library        = /etc/ansible/pluribus-ansible/ansible/library/
#remote_tmp     = $HOME/.ansible/tmp
...
...
# uncomment this to disable SSH key host checking
host_key_checking = False
...
...
# if set, always use this private key file for authentication, same as
# if passing --private-key to ansible or ansible-playbook
#private_key_file = /path/to/file

# If set, configures the path to the Vault password file as an alternative to
# specifying --vault-password-file on the command line.
#vault_password_file = /path/to/vault_password_file
...
...
# You can set these parameters for individual plays in playbooks as well(preferred).
[privilege_escalation] 
#become=True
#become_method=sudo
#become_user=root
#become_ask_pass=False
*** snippet ***
```

# Modules
 Ansible modules reusable, standalone scripts that do the actual work. Modules get called and executed in playbook tasks.
 Modules return information to ansible in JSON format. Modules can be placed in different places where ansible looks for modules. As a convenience, we place them under library folder in our ansible project directory.
 
 **Pluribus Ansible Modules**
   Pluribus-Ansible modules support following configurations. These modules are idempotent. More information about these modules, options and their usage can be found in [Module Docs](/docs/module_docs). 
 
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

 
 Some of these Pluribus modules are included in the Ansible core modules library([Netvisor](http://docs.ansible.com/ansible/list_of_network_modules.html#netvisor)). You will have to clone this repository in your local machine to use other Pluribus modules. 
 To use pluribus-ansible modules or develop modules for pluribus-ansible, clone this repository in the path where you installed ansible. You can have it in a different project directory but make sure you modify the ansible.cfg file with relevant paths. 

```
~$ mkdir <directory-name>
~$ cd <directory-name>
~:<directory-name>$ git clone <url>
~:<directory-name>$ cd pluribus-ansible
~:<directory-name>/pluribus-ansible$ git checkout -b <your branch>
```

Now you can begin working on your branch.

# Playbooks
 Playbooks are Ansible's configuration, deployment and orchestration language. Playbooks are expressed in [YAML](https://docs.ansible.com/ansible/YAMLSyntax.html) format and have a minimum of syntax. Each playbook is composed of one or more plays. The goal of a play is to map a group of hosts to some well defined tasks. A task is basically a call to an Ansible Module. 
 
 **Pluribus Ansible Playbooks**
   Pluribus-Ansible also includes playbooks that use Pluribus modules to apply network configurations. These playbooks can be used to apply configurations with little modifications. These playbooks can also be used as reference/template to create your own playbooks. These playbooks are well organised and documented, describing the modules and parameters with description, and include debug messages, error handling as well as formatted output(pretty printed in JSON format) that describe each and every configuration that is being applied.
   The playbooks are organised in a directory structure, main playbooks in one folder(playbooks) and the playbook variables in vars folder(playbookvariables). The following is an example playbook for initial ZTP setup along with the associated vars file:

```
#Fabric creation
---


# This task is to configure initial ZTP setup on all switches.
# It uses pn_initial_ztp.py module from library/ directory.
# pn_cliusername and pn_clipassword comes from vars file - cli_vault.yml
# If the tasks fails then it will retry as specified by retries count.
- name: Zero Touch Provisioning - Initial setup
  hosts: all
  serial: 1
  become: true
  become_method: su
  become_user: root

  vars_files:
  - ../playbookvariables/cli_vault.yml
  - ../playbookvariables/vars_fabric_creation.yml

  tasks:
    - name: Auto accept EULA, Disable STP, enable ports and create/join fabric
      pn_initial_ztp:
        pn_cliusername: "{{ USERNAME }}"                              # Cli username (value comes from cli_vault.yml).
        pn_clipassword: "{{ PASSWORD }}"                              # Cli password (value comes from cli_vault.yml).
        pn_fabric_name: "{{ pn_fabric_name }}"                        # Name of the fabric to create/join.
        pn_current_switch: "{{ inventory_hostname }}"                 # Name of the switch on which this task is currently getting executed.
        pn_toggle_40g: "{{ pn_toggle_40g }}"                          # Flag to indicate if 40g ports should be converted to 10g ports or not.
        pn_inband_ip: "{{ pn_inband_ip }}"                            # Inband ips to be assigned to switches starting with this value. Default: 172.16.0.0/24.
        pn_fabric_network: "{{ pn_fabric_network }}"                  # Choices: in-band or mgmt.  Default: mgmt
        pn_fabric_control_network: "{{ pn_fabric_control_network }}"  # Choices: in-band or mgmt.  Default: mgmt
        pn_static_setup: "{{ pn_static_setup }}"                      # Flag to indicate if static values should be assign to following switch setup params. Default: True.
        pn_mgmt_ip: "{{ ansible_host }}"                              # Specify MGMT-IP value to be assign if pn_static_setup is True.
        pn_mgmt_ip_subnet: "{{ pn_mgmt_ip_subnet }}"                  # Specify subnet mask for MGMT-IP value to be assign if pn_static_setup is True.
        pn_gateway_ip: "{{ pn_gateway_ip }}"                          # Specify GATEWAY-IP value to be assign if pn_static_setup is True.
        pn_dns_ip: "{{ pn_dns_ip }}"                                  # Specify DNS-IP value to be assign if pn_static_setup is True.
        pn_dns_secondary_ip: "{{ pn_dns_secondary_ip }}"              # Specify DNS-SECONDARY-IP value to be assign if pn_static_setup is True.
        pn_domain_name: "{{ pn_domain_name }}"                        # Specify DOMAIN-NAME value to be assign if pn_static_setup is True.
        pn_ntp_server: "{{ pn_ntp_server }}"                          # Specify NTP-SERVER value to be assign if pn_static_setup is True.
        pn_web_api: "{{ pn_web_api }}"                                # Flag to enable web api. Default: True
        pn_stp: "{{ pn_stp }}"                                        # Specify True if you want to enable STP at the end. Default: False.

      register: ztp_out              # Variable to hold/register output of the above tasks.
      until: ztp_out.failed != true  # If the above code fails it will retry the code
      retries: 3                     # This is the retries count
      delay: 3
      ignore_errors: yes             # Flag to indicate if we should ignore errors if any.

    - debug:
        var: ztp_out.stdout_lines    # Print stdout_lines of register variable.

    - pause:
        seconds: 2                   # Pause playbook execution for specified amount of time.
```

  **and the associated variables file:**
 
```
---
#Fabric creation

pn_fabric_name: 'gui-fabric'                      # mandatory, , Name of the fabric to create/join, Fabric Name, text
pn_toggle_40g: True                               # optional, True:False, Flag to toggle/convert 40g ports to 10g ports, Toggle 40g, boolean
pn_inband_ip: '172.16.1.0/24'                     # optional, 172.16.0.0/24, Inband ips to be assigned to switches starting with this value, Inband IP, text
pn_fabric_network: 'mgmt'                         # optional, in-band:mgmt, Select fabric network type, Fabric Network, text
pn_fabric_control_network: 'mgmt'                 # optional, in-band:mgmt, Select fabric control network, Fabric Control Network, text
pn_static_setup: False                            # optional, True:False, Flag to indicate if static values should be assigned to following switch setup parameters, Static Setup, boolean
pn_mgmt_ip_subnet: '16'                           # optional, , Specify subnet mask for mgmt-ip to be assigned to switches, Mgmt IP Subnet, text
pn_gateway_ip: '10.9.9.0'                         # optional, , Specify gateway-ip to be assigned to switches, Gateway IP, text
pn_dns_ip: '10.20.41.1'                           # optional, , Specify dns-ip to be assigned to switches, DNS IP, text
pn_dns_secondary_ip: '10.20.4.1'                  # optional, , Specify dns-secondary-ip to be assigned to switches, DNS Secondary IP, text
pn_domain_name: 'pluribusnetworks.com'            # optional, , Specify domain-name to be assigned to switches, Domain Name, text
pn_ntp_server: '0.us.pool.ntp.org'                # optional, , Specify ntp-server value to be assigned to switches, NTP Server, text
pn_web_api: True                                  # optional, True:False, Flag to enable web api, Web API, boolean
pn_stp: False                                     # optional, True:False, Flag to enable STP at the end of configuration, STP, boolean 
```
 **Key Points** 
 - The variables file is included under the `vars_files` section by specifying its path relative to the playbook. 
 - The vault file is also included under the `vars_files` section by specifying its path relative to the playbook.(Vault file contains sensitive information like passwords.)
 - Parameters from vault file are accessed as `"{{ USERNAME }}"` and `"{{ PASSWORD }}"`.
 - The variables file is also written in YAML format.
 - Parameters from variables file are accessed as `"{{ pn_fabric_name }}"`.
 - Inventory or host parameters can be passed as `"{{ inventory_hostname }}"` and `"{{ ansible_host }}"`.
 - Hostnames from the inventory/hosts file can also be accessed using filters as `"{{ groups['spine'] }}"` and `"{{ groups['leaf'] }}"`. 
 - Certain modules take a comma separated file(csv file) as a parameter. You can use ansible provided lookup plugin to parse the csv file.
 
 ```
   ...
   ...
  vars_files:
  - ../playbookvariables/cli_vault.yml
  - ../playbookvariables/vars_l3_ztp.yml
  ...
  ...
  ...
       pn_spine_list: "{{ groups['spine'] }}"  # List of all spine switches mentioned under [spine] grp in hosts file.
       pn_leaf_list: "{{ groups['leaf'] }}"    # List of all leaf switches mentioned under [leaf] grp in hosts file.
       pn_csv_data: "{{ lookup('file', '{{ csv_file }}') }}"
  ...
  ...
  
 ```
 
 Following is the list of Pluribus playbooks available and their documentation can be accessed [here](/docs/playbook_docs).
 
 - [pn_initial_ztp.yml](ansible/playbooks/pn_initial_ztp.yml)
 - [pn_l2_ztp.yml](ansible/playbooks/pn_l2_ztp.yml)
 - [pn_l3_ztp.yml](ansible/playbooks/pn_l3_ztp.yml)
 - [pn_vrrp_l2_with_csv.yml](ansible/playbooks/pn_vrrp_l2_with_csv.yml)
 - [pn_l3_vrrp_ebgp.yml](ansible/playbooks/pn_l3_vrrp_ebgp.yml)
 - [pn_l3_vrrp_ospf.yml](ansible/playbooks/pn_l3_vrrp_ospf.yml)
 - [pn_vflow_create.yml](ansible/playbooks/pn_vflow_create.yml)
 - [pn_vxlan.yml](ansible/playbooks/pn_vxlan.yml)
 - [pn_switch_reset.yml](ansible/playbooks/pn_switch_reset.yml)
 - [pn_vlanshow.yml](ansible/roles/examples/pn_vlanshow.yml)
 - [pn_vlancreate.yml](ansible/roles/examples/pn_vlancreate.yml)
 - [pn_vlagcreate.yml](ansible/roles/examples/pn_vlagcreate.yml)
 - [pn_clustercreate.yml](ansible/roles/examples/pn_clustecreate.yml)

**Tip**:[YAML Lint](http://www.yamllint.com/) (online) helps you debug YAML syntax.
 
 
# Security
 Netvisor CLI has a one stage authentication process requiring login credentials to use CLI on devices running ONVL/nvOS. These credentials have to be passed to the Pluribus Ansible modules through playbooks via the parameters `pn_cliusername` and `pn_clipassword`. However it is not a best practice to provide plain-text login credentials for security reasons. These login credentials are not required if root login is enabled on target nodes but this is not recommended unless you have a good reason.
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

# Setup Key Based Authentication
  Ansible is SSH based. It will SSH into the hosts and apply the configurations as specified in the playbook. You will need to specify the remote user flag `-u` as well as `ask-pass or -k` for password everytime you run a playbook. Instead, you can setup SSH keys between your control machine and the target hosts for a more secured connection and avoid the hassle of providing the user and password everytime you run a playbook. You can use the Pluribus module to achieve auto-setup of SSH keys. Use this module+playbook the first time to setup key based authentication.

```
---
# This playbook is to setup SSH keys between localhost and remote switches.
# It uses the pn_autossh module.
# The list of switch IP addresses is passed as a csv file.
# The variables are located in vars_sshkeys.yml file.

- name: Auto SSH setup
  hosts: localhost

  vars_files:
    - ../playbookvariables/cli_vault.yml
    - ../playbookvariables/vars_sshkeys.yml

  tasks:
    - name: Generate SSH keys and push them onto switches
      pn_autossh:
        pn_user: "{{ remote_user }}"                               # Specify the remote user name(SSH user).
        pn_ssh_password: "{{ PASSWORD }}"                          # Specify the SSH password.
        pn_hosts_csv:  "{{ lookup('file', '{{ csv_file }}') }}"    # CSV file that contains (hostname, IP address).
        pn_overwrite: False                                        # Flag that specifies either to overwrite or append the authorization keys file in target hosts.
        pn_filepath: "{{ lookup('env','HOME') + '/.ssh/id_rsa' }}" # Specify the local path to save the generated rsa keys.
      register: output
      
    - debug: var=output.stdout_lines
```
 To setup SSH keys, run the following command:
 
```
$ ansible-playbook pn_autossh.yml --ask-vault-pass
```

# Running Playbooks
   Congratulations, You are now ready to run Pluribus-Ansible playbooks! Just kidding, not yet.
Playbooks can be run using the command `ansible-playbook playbook.yml [options][flags]`. But what are these options and flags?
Let's see the command with the various options/flags:
```
 $ansible-playbook -i hosts playbook.yml -u pluribus -K --ask-pass --ask-vault-pass -vvv 
```
**Options**:
 - **`ansible-playbook`** : The command to run ansible playbook.
 - **`playbook.yml`** : Name of the playbook that you want to run.
 
 **General Options**:
 - **`-i`** : inventory(host) file. 
   - The `-i` flag is followed by the hosts file.
   - Specify the hosts file name  if it is in the same directory as the playbook.
   - Specify the complete path of the hosts file if it is in a different directory.
   - If the `-i` flag is not specified, ansible will consider the hosts file located at `/etc/ansible/hosts`.
 - **`ask-vault-pass`** : ask for vault password when using vault file.
 - **`-v`** : verbose mode(-vv recommended, -vvv for more, -vvvv to enable cnnection debugging).
 
 **Connection Options**:
 - **`-k or --ask-pass`** : (lowercase 'k') ask for connection password.
   - SSH password.
   - Can be provided in the hosts file with vault protection.
   - We recommend setting up SSH key based authentication to avoid using username/password for a more secured connection.  
 - **`-u`** : remote user(generally SSH user, defaults to root!).
   - The `-u` flag is followed by the username.
   - You can specify the username in the hosts file in which case you dont have to provide this flag.
   - You can also set this in the ansible.cfg file(not recommended).
   - We recommend setting up SSH key based authentication to avoid using username/password for a more secured connection. 
   
 **Privilege Escalation Options**:
 - **`-b or --become`** : run operations with become. 
   - We recommend specifying this in the playbook.
 - **`--become-method=BECOME_METHOD`**: privilege escalation method to use.
   - Defaults to sudo. Valid choices: **sudo**, **su**, pbrun, pfexec, doas, dzdo, ksu.
 - **`--become-user=BECOME_USER`** : run operations as this user, defaults to root.
   - We recommend specifying this in the playbook.
 - **`-K or --ask-become-pass`** : (uppercase 'K') ask for privilege escalation password.

Use the flags/options based on your requirements to run the playbooks. 

# Troubleshooting Utilities
  In this section, we describe certain linux utilities that can come in handy while troubleshooting for issues.
  
  **Playbook Logs**
  
  The only way to check the output of the ansible playbook is to use `register` and `debug` modules in playbooks to capture output from the modules. This is because ansible requires module output in JSON format and does not support print statements in module. It is therefore recommended to have some level of verbosity flags while running the playbooks. 
  You can also log the output of the playbook in a log file for later inspection. There are many ways to capture output into log files. Two of them are discussed here:

   - **`I/O redirection`** : Most command line programs that display their results do so by sending their results to standard output. By default, standard output directs its contents to the display. To redirect standard output to a file(overwrite), the `>` character is used.
  
```
  $ ansible-playbook -i hosts playbook.yml -u pluribus -K --ask-pass --ask-vault-pass > playbookoutput.log
```
  or you can use `>>` to append to a file:

```
  $ ansible-playbook -i hosts playbook.yml -u pluribus -K --ask-pass --ask-vault-pass >> playbookoutput.log
```

   - **`tee`** : The I/O redirection only redirects the output to a file, it does not display the output on the screen. Tee command is used to save and view (both at the same time) the output of any command. Tee command writes to the STDOUT, and to a file at a time(`-a` for append):
  
```
  $ ansible-playbook -i hosts playbook.yml -u pluribus -K --ask-pass --ask-vault-pass | tee -a playbookoutput.log  
```
  
  **Execution Time**
  
  You can also time the execution of the playbook by using the linux `time` utility.

```
  $ time ansible-playbook -i hosts playbook.yml -u pluribus -K --ask-pass --ask-vault-pass | tee -a playbookoutput.log
```
 
 This will give the time it took for the playbook to run. 
 
 ```
  real	47m17.075s
  user	6m33.070s
  sys	0m57.437s
 ```
  
  
  
  
  
  
