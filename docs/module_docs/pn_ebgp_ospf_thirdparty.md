# pn_ebgp_ospf_thirdparty

 Zero Touch Provisioning (ZTP) allows you to provision new switches in your network automatically, without manual intervention.

 - [Synopsis](#synopsis)
 - [Options](#options)
 - [Examples](#examples)
 - [Return Values](#return-values)

## Synopsis

  This module allows users to configure L3 VRRP in a mixed network consisting of Leaf switches running Pluribus Netvisor and Spine switches running third party vendor software. This module allows users to configure existing L3 setup with either eBGP or OSPF. The L3 setup is configured using the pn_l3_ztp module. It performs the following tasks based on the routing protocol:
  
  **eBGP**:
  - Assigning bgp_as
  - Configuring bgp_redistribute
  - Configuring bgp_maxpath
  - Assign ebgp_neighbor
  - Assign router_id
  - Create leaf_cluster
  - Add iBGP neighbor for clustered leaf
    
  **OSPF**:
  - Find area_id for leafs
  - Assign ospf_neighbor for leaf cluster
  - Assign ospf_neighbor
  - Assign ospf_redistribute
      
## Options

| parameter        | required       | default       | type        | choices       | comments                                                   |
|------------------|----------------|---------------|-------------|---------------|------------------------------------------------------------|
| pn_cliusername   | see comments   |               | str         |               | Provide login username if user is not root.                |
| pn_clipassword   | see comments   |               | str         |               | Provide login password if user is not root.                |
| pn_spine_list    | yes            |               | list        |               | Specify the list of Spine switches listed under the [spine] group in hosts file. Can be obtained from the hosts file using `"{{ groups['spine'] }}"` filter. |
| pn_leaf_list     | yes            |               | list        |               | Specify the list of Leaf switches listed under the [leaf] group in hosts file. Can be obtained from the hosts file using `"{{ groups['leaf'] }}"` filter. |
| pn_bfd           | no             | False         | bool        |               | Flag to indicate if BFD config should be added to eBGP/OSPF. |
| pn_routing_protocol | yes         |               | str         | ebgp, ospf    | Specify the Routing protocol to configure. |
**eBGP parameters**
| pn_bgp_maxpath   | no             | 16            | str         |               | Specify the BGP-MAXPATH value to be assigned to vrouters. |
| pn_bgp_redistribute | no          | connected     | str         | none, static, connected, rip, ospf | Specify the BGP-REDISTRIBUTE value to be assigned to vrouters. |
| pn_bgp_as_range  | no             | 65000         | str         |               | Specify the BGP-AS range to be assigned to vrouters. |
| pn_ibgp_ip_range | no             | 75.75.75.0/30 | str         |               | Specify the iBGP IP range to be assigned to interfaces. |
| pn_ibgp_vlan     | no             | 4040          | str         |               | Specify the iBGP vlan id to be assigned to interfaces. |
**OSPF parameters**
| pn_ospf_area_id  | no             | 0             | str         |               | Specify the area id to configure for OSPF. |
| pn_iospf_ip_range| no             | 75.75.75.0/30 | str         |               | Specify the IP range for creating the interface between leaf clusters.|
| pn_iospf_vlan    | no             | 4040          | str         |               | Specify the vlan id for creating interface between leaf clusters. |


## Examples

```
---


# This task is to configure eBGP/OSPF.
# It uses pn_ebgp_ospf.py module from library/ directory.
# pn_cliusername and pn_clipassword comes from vars file - cli_vault.yml
# If you don't specify values for pn_bgp_maxpath, pn_bgp_redistribute, pn_bgp_as_range,
# then it will take the default values specified in the pn_ebgp_ospf.py module.
# pn_cliusername and pn_clipassword comes from vault file - cli_vault.yml.
# pn_spine_list and pn_leaf_list comes from the hosts file.
- name: Zero Touch Provisioning - BGP setup
  hosts: spine[0]
  become: true
  become_method: su
  become_user: root

  vars_files:
  - cli_vault.yml

  tasks:
    - name: Configure eBGP
      pn_ebgp_ospf_thirdparty:
        pn_cliusername: "{{ USERNAME }}"                   # Cli username (value comes from cli_vault.yml).
        pn_clipassword: "{{ PASSWORD }}"                   # Cli password (value comes from cli_vault.yml).
        pn_spine_list: "{{ groups['spine'] }}"             # List of all spine switches mentioned under [spine] grp in hosts file.
        pn_leaf_list: "{{ groups['leaf'] }}"               # List of all leaf switches mentioned under [leaf] grp in hosts file.
        pn_bfd: True                                       # Flag to indicate if BFD config should be added to eBGP/ospf. Default: False.
        pn_routing_protocol: 'ebgp'                        # Routing protocol to configure. Choices are ['ebgp', 'ospf']
        pn_bgp_maxpath: '16'                               # BGP-MAXPATH value to be assigned to vrouters. Default: 16
        pn_bgp_redistribute: 'connected'                   # BGP-REDISTRIBUTE value to be assigned to vrouters. Chocies: none, static, connected, rip, ospf. Default: connected
        pn_bgp_as_range: '65000'                           # BGP-AS-RANGE value to be assigned to vrouters. Default: 65000
        pn_ibgp_ip_range: '75.75.75.0/30'                  # iBGP IP range to be assigned to interfaces. Default: '75.75.75.0/30'
        pn_ibgp_vlan: '4040'                               # iBGP vlan value to be assigned to interfaces. Default 4040
        # <<< Following attributes are not needed for eBGP but since OSPF and eBGP are configured using same Ansible module, we are including it here. (Should always be commented out)
        # pn_routing_protocol: 'ospf'                      # Routing protocol to configure. Choices are ['ebgp', 'ospf']
        # pn_ospf_area_id: '0'                             # Area id to configure for ospf. Default: 0
        # pn_iospf_ip_range: '75.75.75.0/30'               # Ip range for creating the interface between leaf clusters. Default:'75.75.75.0/30'
        # pn_iospf_vlan: '4040'                            # Vlan for creating the interface between leaf clusters. Default:'4040'
        # >>> OSPF parameters end here
      register: bgp_out                         # Variable to hold/register output of the above tasks.

    - debug:
        var: bgp_out.stdout_lines               # Print stdout_lines of register variable.
  
```

## Return Values

| name | description | returned | type |
|--------|------------|----------|---------|
| stdout | The set of responses from the CLI configurations. | on success | string |
| stderr | Error message, if any, from the CLI configurations. | on failure | string |
| changed | Indicates whether the module caused changes in the target node.| always | bool |
| failed | Indicates whether the execution failed on the target | always | bool |
