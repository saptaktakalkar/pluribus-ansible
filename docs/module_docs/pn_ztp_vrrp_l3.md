# pn_ztp_vrrp_l3

 Zero Touch Provisioning (ZTP) allows you to provision new switches in your network automatically, without manual intervention.

 - [Synopsis](#synopsis)
 - [Options](#options)
 - [Examples](#examples)
 - [Return Values](#return-values)

## Synopsis

  This module allows users to provision their network devices in a Layer3 or L3 setup, without manual intervention. It also creates VRRP interfaces at the Leaf Layer. Therefore it is required to have atleast 2 Leaf switches with physical links between them for Cluster configuration. This module accepts a comma separated (csv) file in the format specified below. It performs the following tasks:
  
 - Configure Leaf clusters
 - Create vLANs
 - Configure vRouters on Leaf switches
 - Configure VRRP interfaces on the Leaf switches
 - Configure vRouter interfaces on non-cluster Leaf switches.


>## Important Note
  >
  >This module has following pre-requisites:
  >
  >- There are atleast 2 Leaf switches in the topology.
  >- The Leaf switches for VRRP are connected by physical links for cluster configuration.
  >- It is complete clos topology.
  >- The csv file format :  
       For Clustered Leafs: vlanid, ip, leaf-switch1(master), leaf-switch2(slave), vrrp-id, leaf-switc1(master)  
       For Non-Clustered Leafs: vlanid, ip, leaf-switch
      
  Make sure the pre-requisites are met before running the module.

## Options

| parameter        | required       | default       | type        | choices       | comments                                                   |
|------------------|----------------|---------------|-------------|---------------|------------------------------------------------------------|
| pn_cliusername   | see comments   |               | str         |               | Provide login username if user is not root.                |
| pn_clipassword   | see comments   |               | str         |               | Provide login password if user is not root.                |
| pn_spine_list    | yes            |               | list        |               | Specify the list of Spine switches listed under the [spine] group in hosts file. Can be obtained from the hosts file using `"{{ groups['spine'] }}"` filter. |
| pn_leaf_list     | yes            |               | list        |               | Specify the list of Leaf switches listed under the [leaf] group in hosts file. Can be obtained from the hosts file using `"{{ groups['leaf'] }}"` filter. |
| pn_csv_data      | yes            |               | str         |               | Specify the csv file using `lookup` plugin or a string containing data in csv format(vlanid, ip, leaf-switch1(master), leaf-switch2(slave), vrrp-id, leaf-switc1(master)) for clustered leafs and (vlanid, ip, leaf-switch) for non-clustered leafs. |



## Examples
   Sample csv file: `pn_vrrp_l3.csv`
```
100, 172.168.100.0/24, ansible-leaf1, ansible-leaf2, 19, ansible-leaf1
101, 172.168.101.0/24, ansible-leaf3
102, 172.168.102.0/24, ansible-leaf4
104, 172.168.104.0/24, ansible-leaf1, ansible-leaf2, 19, ansible-leaf1
```

```
---

# This task is to configure VRRP for Layer 3 using csv lookup.
# It takes required VRRP config data from csv file.
# Specify the correct 'csv_file' path under vars section.
# It uses pn_ztp_vrrp_l3.py module from library/ directory.
# pn_cliusername and pn_clipassword comes from vars file - cli_vault.yml
# pn_spine_list and pn_leaf_list comes from hosts file
- name: Virtual Router Redundancy Protocol (VRRP) - Layer 3 Setup
  hosts: spine[0]
  become: true
  become_method: su
  become_user: root

  vars_files:
  - cli_vault.yml

  vars:
  - csv_file: /etc/ansible/pluribus-ansible/ansible/pn_vrrp_l3.csv  # CSV file path

  tasks:
    - name: Configure VRRP L3 setup
      pn_ztp_vrrp_l3:
        pn_cliusername: "{{ USERNAME }}"  # Cli username (value comes from cli_vault.yml).
        pn_clipassword: "{{ PASSWORD }}"  # Cli password (value comes from cli_vault.yml).
        pn_spine_list: "{{ groups['spine'] }}"  # List of all spine switches mentioned under [spine] grp in hosts file.
        pn_leaf_list: "{{ groups['leaf'] }}"    # List of all leaf switches mentioned under [leaf] grp in hosts file.
        pn_csv_data: "{{ lookup('file', '{{ csv_file }}') }}"  # VRRP Layer3 data specified in CSV file.
      register: vrrp_out               # Variable to hold/register output of the above tasks.

    - debug:
        var: vrrp_out.stdout_lines     # Print stdout_lines of register variable.
  
```

## Return Values

| name | description | returned | type |
|--------|------------|----------|---------|
| stdout | The set of responses from the CLI configurations. | on success | string |
| stderr | Error message, if any, from the CLI configurations. | on failure | string |
| changed | Indicates whether the module caused changes in the target node.| always | bool |
| failed | Indicates whether the execution failed on the target | always | bool |
