# pn_vrouterif

 Module for CLI vrouter-interface configurations. Supports `vrouter-interface-add` and `vrouter-interface-remove` commands with options.

 - [Synopsis](#synopsis)
 - [Options](#options)
 - [Usage](#usage)
 - [Examples](#examples)
 - [Return Values](#return-values)

## Synopsis

  Each fabric, cluster, standalone switch, or virtual network (VNET) can provide its tenants with a virtual router (vRouter) service that forwards traffic between networks and implements Layer 3 protocols.
  For a complete discussion of all the features, please refer to the Pluribus Networks technical product documentation.
  
## Options

| parameter       | required       | default      | type        | choices       | comments                                                   |
|-----------------|----------------|--------------|-------------|---------------|------------------------------------------------------------|
| pn_cliusername  | see comments   |              | str         |               | Provide login username if user is not root.                |
| pn_clipassword  | see comments   |              | str         |               | Provide login password if user is not root.                |
| pn_cliswitch    | no             | local        | str         |               | Target switch(es) to run command on.                       |
| pn_command      | yes            |              | str         | vrouter-interface-add, vrouter-interface-remove| add, remove vrouter interface configurations.|
| pn_vrouter_name | yes            |              | str         |               | Specify the name of the vRouter.                           |
| pn_vlan         | no             |              | int         |               | Specify the VLAN identifier. This is a value between 1 and 4092.|
| pn_interface_ip | for vrouter-interface-add|    | str         |               | Specify the IP address of the interface in x.x.x.x/n format.| 
| pn_assignment   | no             |              | str         | none, dhcp, dhcpv6, autov6| Specify the DHCP method for IP address assignment.|
| pn_vxlan        | no             |              | int         |               | Specify the VXLAN identifier. This is a value between 1 and 16777215.                            |
| pn_interface    | no             |              | str         | mgmt, data, span| Specify if the interface is management, data or span interface.|
| pn_alias        | no             |              | str         |               | Specify an alias for the interface.         |
| pn_exclusive    | no             |              | bool        | True, False   | Specify if the interface is exclusive to the configuration. Exclusive means that other configurations cannot use the interface. Exclusive is specified when you configure the interface as span interface and allows higher throughput through the interface.        |
| pn_nic_enable   | no             |              | bool        | True, False   | Specify if the NIC is enabled or not.               |
| pn_vrrp_id      | no             |              | int         |               | Specify the ID for the VRRP interface. The IDs on both vRouters must be the same IS number.                |
| pn_vrrp_priority| no             |              | int         |               | Speicfies the priority for the VRRP interface. This is a value between 1 (lowest) and 255 (highest).|
| pn_vrrp_adv_int | no             |              | str         |               | Specify a VRRP advertisement interval in milliseconds. The range is from 30 to 40950 with a default value of 1000.                    |
| pn_l3port       | no             |              | str         |               | Specify a Layer 3 port for the interface.|
| pn_secondary_macs| no            |              | str         |               | Specify a secondary MAC address for the interface.|
| pn_nic_str      | for vrouter-interface-remove| | str         |               | Specify the NIC of the interface. Used for vrouter-interface remove.             |

## Usage

```
- name: "Playbook for CLI vRouter interface"
  hosts: <hosts>
  user: <user>
  
  vars_files:
  - foo_vault.yml
  
  tasks:
  - name: "PN vRouter interface command"
    pn_vrouterif: >
      [pn_cliusername: <username>] 
      [pn_clipassword: <password>] 
      pn_command: <vrouter-interface-add/remove/modify> 
      pn_vrouter_name: <name>
      [pn_interface_ip: <neighbor ip>]
  
```

## Examples

# vrouter-interface-add
Sample playbook for **_adding_** interface to vRouter configuration with `user: pluribus`.

Equivalent CLI:
```
CLI......> vrouter-interface-add vrouter-name ansible-vrouter ip 102.102.102.1/24 if data
```

```
---
- name: "Playbook for vRouter interface add"
  hosts: spine[0]
  user: pluribus
  
  vars_files:
  - foo_vault.yml 
  
  tasks:
  - name: "Add vRouter interface"
    pn_vrouterif: 
      pn_cliusername: "{{ USERNAME }}" 
      pn_clipassword: "{{ PASSWORD }}"
      pn_command: vrouter-interface-add 
      pn_vrouter_name: ansible-vrouter 
      pn_interface_ip: 102.102.102.1/24 
      pn_interface: data
    register: cmd_output
  - debug: var: cmd_output
  
```

# vrouter-interface-remove
Sample playbook for **_removing_** interface from vRouter configuration with `user: root`.

Equivalent CLI:
```
CLI......> vrouter-interface-remove vrouter-name ansible-vrouter nic_str eth12.100
```

```
---
- name: "Playbook for vRouter interface remove"
  hosts: spine[0]
  user: root
  
  tasks:
  - name: "remove vrouter"
    pn_vrouterif: 
      pn_command: vrouter-interface-remove 
      pn_vrouter_name: ansible-vrouter 
      pn_nic_str: eth12.100
    register: cmd_output
  - debug: var=cmd_output
  
```

## Return Values

| name | description | returned | type |
|--------|------------|----------|---------|
| command | The CLI command run on target nodes. | always | string |
| stdout | Output of the CLI command. | on success | string |
| stderr | Error message from the CLI command. | on failure | string |
| changed | Indicates whether the CLI caused changes in the target node.| always | bool |
