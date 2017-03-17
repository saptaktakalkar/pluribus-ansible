# pn_ztp_vrrp_l2_csv

 Zero Touch Provisioning (ZTP) allows you to provision new switches in your network automatically, without manual intervention.

 - [Synopsis](#synopsis)
 - [Options](#options)
 - [Examples](#examples)
 - [Return Values](#return-values)

## Synopsis

  This module allows users to provision their network devices in a Layer2 or L2 setup, without manual intervention. It also creates VRRP interfaces at the Spine Layer. Therefore it is required to have 2 Spine switches with physical links between them for Cluster configuration. This module accepts a comma separated (csv) file in the format (ip, vlanid, spine-switch-name). It performs the following tasks:
  
 - Configure Spine clusters
 - Create vLANs
 - Configure vRouters on Spine switches
 - Configure VRRP interfaces on the Spine switches


>## Important Note
  >
  >This module has following pre-requisites:
  >
  >- There are only 2 Spine switches in the topology.
  >- The Spine switches are connected by physical links for cluster configuration.
  >- It is complete clos topology.
  >- The csv file format : ip, vlanid, spine-switch-name
  
  Make sure the pre-requisites are met before running the module.

## Options

| parameter        | required       | default       | type        | choices       | comments                                                   |
|------------------|----------------|---------------|-------------|---------------|------------------------------------------------------------|
| pn_cliusername   | see comments   |               | str         |               | Provide login username if user is not root.                |
| pn_clipassword   | see comments   |               | str         |               | Provide login password if user is not root.                |
| pn_spine_list    | yes            |               | list        |               | Specify the list of Spine switches listed under the [spine] group in hosts file. Can be obtained from the hosts file using `"{{ groups['spine'] }}"` filter. |
| pn_leaf_list     | yes            |               | list        |               | Specify the list of Leaf switches listed under the [leaf] group in hosts file. Can be obtained from the hosts file using `"{{ groups['leaf'] }}"` filter. |
| pn_vrrp_id       | no             | 18            | str         |               | Specify the VRRP ID to be assigned to the vRouters. |
| pn_csv_data      | yes            |               | str         |               | Specify the csv file using `lookup` plugin or a string containing data in csv format(ip, vlanid, spine-switch-name). |



## Examples
   Sample csv file: `pn_vrrp_l2.csv`
```
101.108.100.0/24, 100, ansible-spine1
101.108.101.0/24, 101, ansible-spine1
101.108.102.0/24, 102, ansible-spine2
101.108.103.0/24, 103, ansible-spine2
```

```
---


# This task is to configure VRRP for Layer 2 using csv lookup.
# It takes required VRRP config data from csv file.
# Specify the correct 'csv_file' path under vars section.
# It uses pn_ztp_vrrp_l2_csv.py module from library/ directory.
# pn_cliusername and pn_clipassword comes from vars file - cli_vault.yml.
# pn_spine_list and pn_leaf_list comes from the hosts file.
- name: Virtual Router Redundancy Protocol (VRRP) - Layer 2 Setup
  hosts: spine[0]
  become: true
  become_method: su
  become_user: root

  vars_files:
  - cli_vault.yml

  vars:
  - csv_file: /etc/ansible/pluribus-ansible/ansible/pn_vrrp_l2.csv  # CSV file path.

  tasks:
    - name: Configure VRRP L2
      pn_ztp_vrrp_l2_csv:
        pn_cliusername: "{{ USERNAME }}"        # Cli username (value comes from cli_vault.yml).
        pn_clipassword: "{{ PASSWORD }}"        # Cli password (value comes from cli_vault.yml).
        pn_spine_list: "{{ groups['spine'] }}"  # List of all spine switches mentioned under [spine] grp in hosts file.
        pn_leaf_list: "{{ groups['leaf'] }}"    # List of all leaf switches mentioned under [leaf] grp in hosts file.
        pn_vrrp_id: '18'                        # Specify VRRP ID to be assigned. Default: 18.
        pn_csv_data: "{{ lookup('file', '{{ csv_file }}') }}"  # VRRP layer2 data specified in csv file.
      register: vrrp_out                        # Variable to hold/register output of the above tasks.

    - debug:
        var: vrrp_out.stdout_lines              # Print stdout_lines of register variable.
  
```

## Return Values

| name | description | returned | type |
|--------|------------|----------|---------|
| stdout | The set of responses from the CLI configurations. | on success | string |
| stderr | Error message, if any, from the CLI configurations. | on failure | string |
| changed | Indicates whether the module caused changes in the target node.| always | bool |
| failed | Indicates whether the execution failed on the target | always | bool |
