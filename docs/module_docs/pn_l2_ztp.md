# pn_l2_ztp

 Zero Touch Provisioning (ZTP) allows you to provision new switches in your network automatically, without manual intervention.

 - [Synopsis](#synopsis)
 - [Options](#options)
 - [Examples](#examples)
 - [Return Values](#return-values)

## Synopsis

  This module allows users to provision their network devices in a Layer2 or L2 setup, without manual intervention. It performs the following tasks:
  
 - Configure Auto vlag between switches: 
   - Configure clusters
   - Trunks
   - vLags 
 - Modify STP
      
## Options

| parameter        | required       | default       | type        | choices       | comments                                                   |
|------------------|----------------|---------------|-------------|---------------|------------------------------------------------------------|
| pn_cliusername   | see comments   |               | str         |               | Provide login username if user is not root.                |
| pn_clipassword   | see comments   |               | str         |               | Provide login password if user is not root.                |
| pn_spine_list    | yes            |               | list        |               | Specify the list of Spine switches listed under the [spine] group in hosts file. Can be obtained from the hosts file using `"{{ groups['spine'] }}"` filter. |
| pn_leaf_list     | yes            |               | list        |               | Specify the list of Leaf switches listed under the [leaf] group in hosts file. Can be obtained from the hosts file using `"{{ groups['leaf'] }}"` filter. |
| pn_update_fabric_to_inband | no   | False         | bool        |               | Flag to indicate if fabric network should be updated to in-band or not. |
| pn_stp | no | False | bool | | Flag to enable STP at the end. |



## Examples

```
---


# This task is to configure ZTP layer 2 setup.
# It uses pn_l2_ztp.py module from library/ directory.
# pn_cliusername and pn_clipassword comes from vault file - cli_vault.yml.
# pn_spine_list and pn_leaf_list comes from the hosts file.
- name: Zero Touch Provisioning - Layer2 setup
  hosts: spine[0]
  become: true
  become_method: su
  become_user: root

  vars_files:
  - cli_vault.yml

  tasks:
    - name: Configure auto vlag
      pn_l2_ztp:
        pn_cliusername: "{{ USERNAME }}"        # Cli username (value comes from cli_vault.yml).
        pn_clipassword: "{{ PASSWORD }}"        # Cli password (value comes from cli_vault.yml).
        pn_spine_list: "{{ groups['spine'] }}"  # List of all spine switches mentioned under [spine] grp in hosts file.
        pn_leaf_list: "{{ groups['leaf'] }}"    # List of all leaf switches mentioned under [leaf] grp in hosts file.
        # pn_update_fabric_to_inband: False     # Flag to indicate if fabric network should be updated to in-band. Default: False.
        # pn_stp: False                         # Specify True if you want to enable STP at the end. Default: False.

      register: ztp_l2_out                      # Variable to hold/register output of the above tasks.

    - debug:
        var: ztp_l2_out.stdout_lines            # Print stdout_lines of register variable.
  
```

## Return Values

| name | description | returned | type |
|--------|------------|----------|---------|
| stdout | The set of responses from the CLI configurations. | on success | string |
| stderr | Error message, if any, from the CLI configurations. | on failure | string |
| changed | Indicates whether the module caused changes in the target node.| always | bool |
| failed | Indicates whether the execution failed on the target | always | bool |
