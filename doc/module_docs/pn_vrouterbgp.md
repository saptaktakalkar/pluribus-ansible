# pn_vrouterbgp

 Module for CLI vrouter-bgp configurations. Supports `vrouter-bgp-add`, `vrouter-bgp-remove` and `vrouter-bgp-modify` commands with options.

 - [Synopsis](#synopsis)
 - [Options](#options)
 - [Usage](#usage)
 - [Examples](#examples)
 - [Return Values](#return-values)

## Synopsis

  Each fabric, cluster, standalone switch, or virtual network (VNET) can provide its tenants with a virtual router (vRouter) service that forwards traffic between networks and implements Layer 3 protocols.
  
## Options

| parameter       | required       | default      |choices       |comments                                                    |
|-----------------|----------------|--------------|--------------|------------------------------------------------------------|
| pn_cliusername  | yes            |              |              | Login username.                                            |
| pn_clipassword  | yes            |              |              | Login password.                                            |
| pn_cliswitch    | no             |              |              | Target switch(es) to run command on.                       |
| pn_command      | yes            |              | vrouter-bgp-add, vrouter-bgp-remove, vrouter-bgp-modify | add, remove, modify vrouter configurations.|
| pn_vrouter_name | yes            |              |              | Specify the name of the vRouter.                           |
| pn_neighbor     | yes            |              |              | Specify the neighbor IP address to use for BGP.            |
| pn_remote_as    | for vrouter-bgp-add |         |              | Specify the remote Autonomous System(AS) number. This value is between 1 and 4294967295.| 
| pn_next_hop_self| no             |              | True, False  | Specify if the next hop is the same router or not.         |
| pn_password     | no             |              |              | Specify a password, if desired.                            |
| pn_ebgp         | no             |              |              | Specifies a value for external BGP to accept or attempt BGP connections to external peers, not directly connected, on the network. This is a value between 1 and 255.|
| pn_prefix_listin| no             |              |              | Specify the prefix list to filter traffic inbound.         |
| pn_prefix_listout| no            |              |              | Specify the prefix list to filter traffic outbound.        |
| pn_route_reflector| no           |              | True, False  | Specify if a route reflector client is used.               |
| pn_override_capability| no       |              | True, False  | Specify if you want to override capability.                |
| pn_soft_reconfig| no             |              | True, False  | Specify if you want soft reconfiguration of inbound traffic.|
| pn_max_prefix   | no             |              |              | Specify the maximum number of prefixes.                    |
| pn_max_prefix_warn| no           |              | True, False  | Specify if you want a warning message when the maximum number of prefixes is exceeded.|
| pn_bfd          | no             |              | True, False  | Specify if you want BFD protocol support for fault detection.|
| pn_multiprotocol| no             |              | ipv4-unicast, ipv6-unicast| Specify a multi protocol for BGP.             |
| pn_weight       | no             |              |              | Specify a default weight value between 0 and 65535 for the neighbor.|
| pn_default_originate| no         |              | True, False  | Specify if you want to announce default routes to the neighbor or not.|
| pn_keepalive    | no             |              |              | Specify BGP neighbor keepalive interval in seconds.        |
| pn_holdtime     | no             |              |              | Specify BGP neighbor holdtime in seconds.                  |
| pn_route_mapin  | no             |              |              | Specify inbound route map for neighbor.                    |
| pn_route_mapout | no             |              |              | Specify outbound route map for neighbor.                   |
| pn_quiet        | no             | true         |              | Enable/disable system information.                         |


## Usage

```
- name: "Playbook for CLI vRouter BGP"
  hosts: <hosts>
  user: <user>
  
  tasks:
  - name: "PN vRouter BGP command"
    pn_vrouterbgp: >
      pn_cliusername=<username> 
      pn_clipassword=<password> 
      pn_command=<vrouter-bgp-add/remove/modify> 
      pn_vrouter_name=<name>
      pn_neighbor=<neighbor ip>
      [pn_remote_as=<remote AS number>]
      [pn_quiet=<True/False>]
  
```

## Examples

# vrouter-bgp-add
Sample playbook for **_adding_** BGP to vRouter configuration.

```
---
- name: "Playbook for vRouter BGP add"
  hosts: spine[0]
  user: root
  tasks:
  - name: "Add vRouter BGP"
    pn_vrouterbgp: pn_cliusername=<username> pn_clipassword=<password> pn_command='vrouter-bgp-add' pn_vrouter_name='ansible-vrouter' pn_neighbor='102.102.102.1' pn_remote_as=65000
    register: cmd_output
  - debug: var=cmd_output
  
```

# vrouter-bgp-remove
Sample playbook for **_removing_** BGP from vRouter configuration.

```
---
- name: "Playbook for vRouter BGP remove"
  hosts: spine[0]
  user: root
  tasks:
  - name: "remove vrouter"
    pn_vrouterbgp: pn_cliusername=<username> pn_clipassword=<password> pn_command='vrouter-bgp-remove' pn_vrouter_name='ansible-vrouter' pn_neighbor='102.102.102.1'
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
