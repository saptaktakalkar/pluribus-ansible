# pn_ospf

 Module for CLI vrouter-ospf configurations. Supports `vrouter-ospf-add` and `vrouter-ospf-remove` commands with options.

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
| pn_command      | yes            |              | vrouter-ospf-add, vrouter-ospf-remove| Add or remove OSPF to/from vRouter configurations.|
| pn_vrouter_name | yes            |              |              | Specify the name of the vRouter name.                      |
| pn_network_ip   | yes            |              |              | Specify the network IP address.                            |
| pn_netmask      | for vrouter-ospf-add |        |              | Specify the netmask of the IP address.                     |
| pn_ospf_area    | for vrouter-ospf-add |        |              | Specify the Stub area number of the configuration.         |
| pn_quiet        | no             | true         |              | Enable/disable system information.                         |


## Usage

```
- name: "Playbook for CLI vRouter OSPF"
  hosts: <hosts>
  user: <user>
  
  tasks:
  - name: "PN vRouter OSPF command"
    pn_ospf: >
      pn_cliusername=<username> 
      pn_clipassword=<password> 
      pn_command=<vrouter-ospf-add/remove> 
      pn_vrouter_name=<name>
      pn_network_ip=<network ip>
      [pn_netmask=<netmask>]
      [pn_ospf_area=<ospf area number>]
      [pn_quiet=<True/False>]
  
```

## Examples

# vrouter-ospf-add
Sample playbook for **_adding_** OSPF to vRouter configuration.

```
---
- name: "Playbook for vRouter OSPF add"
  hosts: spine[0]
  user: root
  tasks:
  - name: "Add vRouter OSPF"
    pn_ospf: pn_cliusername=<username> pn_clipassword=<password> pn_command='vrouter-ospf-add' pn_vrouter_name='ansible-vrouter' pn_network_ip='102.102.102.1' pn_netmask=255.255.255.0 pn_ospf_area=0
    register: cmd_output
  - debug: var=cmd_output
  
```

# vrouter-ospf-remove
Sample playbook for **_removing_** OSPF from vRouter configuration.

```
---
- name: "Playbook for vRouter OSPF remove"
  hosts: spine[0]
  user: root
  tasks:
  - name: "remove vrouter"
    pn_ospf: pn_cliusername=<username> pn_clipassword=<password> pn_command='vrouter-ospf-remove' pn_vrouter_name='ansible-vrouter' pn_network_ip='102.102.102.1'
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
