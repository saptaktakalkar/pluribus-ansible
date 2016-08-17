# pn_ospf

 Module for CLI vrouter-ospf configurations. Supports `vrouter-ospf-add` and `vrouter-ospf-remove` commands with options.

 - [Synopsis](#synopsis)
 - [Options](#options)
 - [Usage](#usage)
 - [Examples](#examples)
 - [Return Values](#return-values)

## Synopsis

  Each fabric, cluster, standalone switch, or virtual network (VNET) can provide its tenants with a virtual router (vRouter) service that forwards traffic between networks and implements Layer 3 protocols.
  For a complete discussion of all the features, please refer to the Pluribus Networks technical product documentation.
  
## Options

| parameter       | required       | default      | type         | choices      |comments                                    |
|-----------------|----------------|--------------|--------------|--------------|--------------------------------------------|
| pn_cliusername  | see comments   |              | str          |              | Provide login username if user is not root.|
| pn_clipassword  | see comments   |              | str          |              | Provide login password if user is not root |
| pn_cliswitch    | no             | local        | str          |              | Target switch(es) to run command on.       |
| pn_command      | yes            |              | str          | vrouter-ospf-add, vrouter-ospf-remove| Add or remove OSPF to/from vRouter configurations.|
| pn_vrouter_name | yes            |              | str          |              | Specify the name of the vRouter name.      |
| pn_network_ip   | yes            |              | str          |              | Specify the network IP address in x.x.x.x/n format.|
| pn_ospf_area    | for vrouter-ospf-add |        | str          |              |Specify the Stub area number of the configuration.|


## Usage

```
- name: "Playbook for CLI vRouter OSPF"
  hosts: <hosts>
  user: <user>
  
  vars_files:
  - foo_vault.yml
  
  tasks:
  - name: "PN vRouter OSPF command"
    pn_ospf: 
      [pn_cliusername: <username>] 
      [pn_clipassword: <password>] 
      pn_command: <vrouter-ospf-add/remove> 
      pn_vrouter_name: <name>
      pn_network_ip: <network ip>
      [pn_ospf_area: <ospf area number>]
  
```

## Examples

# vrouter-ospf-add
Sample playbook for **_adding_** OSPF to vRouter configuration with `user: pluribus`.

Equivalent CLI:
```
CLI......> vrouter-ospf-add vrouter-name ansible-vrouter network 102.102.102.1/24 ospf-area 0
```


```
---
- name: "Playbook for vRouter OSPF add"
  hosts: spine[0]
  user: pluribus
  
  vars_files:
  - foo_vault.yml
  
  tasks:
  - name: "Add vRouter OSPF"
    pn_ospf: 
      pn_cliusername: "{{ USERNAME }}" 
      pn_clipassword: "{{ PASSWORD }}" 
      pn_command: vrouter-ospf-add 
      pn_vrouter_name: ansible-vrouter 
      pn_network_ip: 102.102.102.1/24
      pn_ospf_area: 0
    register: cmd_output
  - debug: var=cmd_output
  
```

# vrouter-ospf-remove
Sample playbook for **_removing_** OSPF from vRouter configuration with `user: root`.

Equivalent CLI:
```
CLI......> vrouter-ospf-remove vrouter-name ansible-vrouter network 102.102.102.1/24
```

```
---
- name: "Playbook for vRouter OSPF remove"
  hosts: spine[0]
  user: root
  
  
  tasks:
  - name: "remove vrouter"
    pn_ospf: 
      pn_command: vrouter-ospf-remove 
      pn_vrouter_name: ansible-vrouter 
      pn_network_ip: 102.102.102.1/24
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


