# pn_l3_ztp_thirdparty

 Zero Touch Provisioning (ZTP) allows you to provision new switches in your network automatically, without manual intervention.

 - [Synopsis](#synopsis)
 - [Options](#options)
 - [Examples](#examples)
 - [Return Values](#return-values)

## Synopsis

  This module allows users to configure L3 VRRP in a mixed network consisting of Leaf switches running Pluribus Netvisor and Spine switches running third party vendor software. This module allows users to provision their network devices in a Layer3 or L3 setup, without manual intervention. It performs the following tasks:
  
 - Auto configure link IPs: 
   - Configure vRouters
   - Modify Trunk settings
   - Configure vRouter L3 interfaces 
   - Configure vRouter Loopback interfaces
 - Modify STP
      
## Options

| parameter        | required       | default       | type        | choices       | comments                                                   |
|------------------|----------------|---------------|-------------|---------------|------------------------------------------------------------|
| pn_cliusername   | see comments   |               | str         |               | Provide login username if user is not root.                |
| pn_clipassword   | see comments   |               | str         |               | Provide login password if user is not root.                |
| pn_leaf_list     | yes            |               | list        |               | Specify the list of Leaf switches listed under the [leaf] group in hosts file. Can be obtained from the hosts file using `"{{ groups['leaf'] }}"` filter. |
| pn_spine_list    | yes            |               | list        |               | Specify the list of Spine switches listed under the [spine] group in hosts file. Can be obtained from the hosts file using `"{{ groups['spine'] }}"` filter. |
| pn_net_address   | yes            |               | str         |               | Specify the network address to calculate link IPs for layer3 fabric. |
| pn_cidr          | yes            |               | str         |               | Specify the subnet mask to calculate link IPs for layer3 fabric. |
| pn_supernet      | yes            |               | str         |               | Specify the supernet mask to calculate link IPs for layer3 fabric. |
| pn_assign_loopback | no           | False         | bool        |               | Flag to indicate if loopback IPs should be assigned to vrouters in layer3 fabric. |
| pn_loopback_ip   | no             | 109.109.109.0/24 | str      |               | Specify the loopback IP value for vrouters in layer3 fabric. |
| pn_bfd           | no             | False         | bool        |               | Flag to indicate if BFD config should be added to vrouter interfaces in case of layer3 fabric. |
| pn_bfd_min_rx    | no             | 30            | str         |               | Specify the BFD minimum receive interval value for adding BFD configuration to vrouter interfaces. |
| pn_bfd_multiplier| no             | 3             | str         |               | Specify the BFD detection multiplier value for adding BFD configuration to vrouter interfaces. |
| pn_update_fabric_to_inband | False| False         | bool        |               | Flag to indicate if fabric network should be updated to in-band or not. |
| pn_stp | no(\*) | False | bool | | Flag to enable STP at the end. |


## Examples

```
---


# This task is to configure ZTP layer 3 setup.
# It uses pn_l3_ztp.py module from library/ directory.
# pn_cliusername and pn_clipassword comes from vault file - cli_vault.yml.
# pn_spine_list and pn_leaf_list comes from the hosts file.
- name: Zero Touch Provisioning - Layer3 setup
  hosts: spine[0]
  become: true
  become_method: su
  become_user: root

  vars_files:
  - cli_vault.yml

  tasks:
    - name: Auto configure link IPs
      pn_l3_ztp_thirdparty:
        pn_cliusername: "{{ USERNAME }}"        # Cli username (value comes from cli_vault.yml).
        pn_clipassword: "{{ PASSWORD }}"        # Cli password (value comes from cli_vault.yml).
        pn_spine_list: "{{ groups['spine'] }}"  # List of all spine switches mentioned under [spine] grp in hosts file.
        pn_leaf_list: "{{ groups['leaf'] }}"    # List of all leaf switches mentioned under [leaf] grp in hosts file.
        pn_net_address: '172.168.1.0'           # Network address required to calculate link IPs for layer3 fabric.
        pn_cidr: '24'                           # Subnet mask required to calculate link IPs for layer3 fabric.
        pn_supernet: '30'                       # Supernet mask required to calculate link IPs for layer3 fabric.
        pn_assign_loopback: True                # Flag to indicate if loopback ips should be assigned to vrouters in layer3 fabric. Default: False.
        pn_loopback_ip: '109.109.109.0/24'    # Loopback ip value for vrouters in layer3 fabric. Default: 109.109.109.0/24.
        pn_bfd: True                          # Flag to indicate if BFD config should be added to vrouter interfaces in case of layer3 fabric. Default: False.
        pn_bfd_min_rx: 200                    # BFD-MIN-RX value required for adding BFD configuration to vrouter interfaces.
        pn_bfd_multiplier: 3                  # BFD_MULTIPLIER value required for adding BFD configuration to vrouter interfaces.
        pn_update_fabric_to_inband: False     # Flag to indicate if fabric network should be updated to in-band. Default: False.
        pn_stp: True                          # Flag to enable STP. Default: True.

      register: ztp_l3_out                      # Variable to hold/register output of the above tasks.

    - debug:
        var: ztp_l3_out.stdout_lines            # Print stdout_lines of register variable.
  
```

## Return Values

| name | description | returned | type |
|--------|------------|----------|---------|
| stdout | The set of responses from the CLI configurations. | on success | string |
| stderr | Error message, if any, from the CLI configurations. | on failure | string |
| changed | Indicates whether the module caused changes in the target node.| always | bool |
| failed | Indicates whether the execution failed on the target | always | bool |
