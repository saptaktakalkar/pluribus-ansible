# pn_vlag

 Module for CLI vlag configurations. Supports `vlag-create`, `vlag-delete` and `vlag-modify` commands with options.

 - [Synopsis](#synopsis)
 - [Options](#options)
 - [Usage](#usage)
 - [Examples](#examples)
 - [Return Values](#return-values)

## Synopsis

  A virtual link aggregation group (VLAG) allows links that are physically connected to two different Pluribus Networks devices to appear as a single
  trunk to a third device. The third device can be a switch, server, or any Ethernet device. A VLAG can provide Layer 2 multipathing, which allows you
  to create redundancy by increasing bandwidth, enabling multiple parallel paths between nodes and loadbalancing traffic where alternative paths exist.
  For a complete discussion of all the features, please refer to the Pluribus Networks technical product documentation.
## Options

| parameter        | required       | default       | type        | choices       | comments                                                   |
|------------------|----------------|---------------|-------------|---------------|------------------------------------------------------------|
| pn_cliusername   | see comments   |               | str         |               | Provide login username if user is not root.                |
| pn_clipassword   | see comments   |               | str         |               | Provide login password if user is not root.                |
| pn_cliswitch     | no             | local         | str         |               | Target switch(es) to run command on.                       |
| pn_command       | yes            |               | str         | vlag-create, vlag-delete, vlag-modify | Create, delete or modify VLAGs.   |
| pn_name          | yes            |               | str         |               | Specify the name for the VLAG.                             |
| pn_port          | for vlag-create|               | str         |               | Specify the local VLAG port.                               |
| pn_peer_port     | for vlag-create|               | str         |               | Specify the peer VLAG port.                                |
| pn_mode          | no             |               | str         | active-active, active-standby | Specify the VLAG mode.                    |
| pn_peer_switch   | for vlag-create|               | str         |               | Specify the fabric-name of the peer-switch.                |
| pn_failover_action  | no          |               | str         | move, ignore  | Specify the failover action as move or ignore.             |
| pn_lacp_mode     | no             |               | str         | off, passive, active | Specify the LACP mode.                             |
| pn_lacp_timeout  | no             |               | str         | slow, fast    | Specify the LACP timeout as slow(30s) or fast(4s).         |
| pn_lacp_fallback | no             |               | str         | individual, bundled | Specify the LACP fallback mode.                     | 
| pn_lacp_fallback_timeout | no     |               | str         |               | The LACP fallback timeout in seconds. Range is between 30s to 60s.|


## Usage

```
- name: "Playbook for CLI VLAG"
  hosts: <hosts>
  user: <user>
  
  vars_files:
  - foo_vault.yml
  
  tasks:
  - name: "PN VLAG command"
    pn_vlag: 
      [pn_cliusername: <username>]
      [pn_clipassword: <password>]
      pn_command: <vlag-create/delete/modify> 
      pn_name: <name>  
      [pn_port: <vlag name>] 
      [pn_peer_port: <peer port>] 
      [pn_mode: <active-active/active-standby>] 
      [pn_peer_switch: <peer switch name>] 
  
```

## Examples

# cluster-create
Sample playbook for **_creating_** VLAG configuration with `user: pluribus`.

Equivalent CLI:
```
CLI......> vlag-create name spine-to-leaf1 port spine1-to-leaf1 peer-port spine2-to-leaf1 peer-switch spine2 mode active-active
```

```
---
- name: Playbook for VLAG Create
  hosts: spine[0]
  user: pluribus
  tasks:
  - name: Create VLAG
    pn_vlag: 
      pn_cliusername: "{{ USERNAME }}" 
      pn_clipassword: "{{ PASSWORD }}"
      pn_command: vlag-create 
      pn_name: spine-to-leaf1 
      pn_port: spine1-to-leaf1
      pn_peer_switch: spine2
      pn_peer_port: spine2-to-leaf1 
      pn_mode: active-active
    register: cmd_output
  - debug: var=cmd_output
  
```

# cluster-delete
Sample playbook for **_deleting_** VLAG configuration with `user: root`.

Equivalent CLI:
```
CLI......> vlag-delete name spine-to-leaf1
```

```
---
- name: Playbook for VLAG Delete
  hosts: spine[0]
  user: root
  
  tasks:
  - name: Delete VLAGs
    pn_vlag: 
      pn_command: vlag-delete 
      pn_name: spine-to-leaf1
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

