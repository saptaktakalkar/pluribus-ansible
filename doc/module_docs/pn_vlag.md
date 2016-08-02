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
 
## Options

| parameter        | required       | default      |choices       |comments                                                    |
|------------------|----------------|--------------|--------------|------------------------------------------------------------|
| pn_cliusername   | yes            |              |              | Login username.                                            |
| pn_clipassword   | yes            |              |              | Login password.                                            |
| pn_cliswitch     | no             |              |              | Target switch(es) to run command on.                       |
| pn_command       | yes            |              | vlag-create, vlag-delete, vlag-modify | Create, delete or modify VLAGs.   |
| pn_name          | yes            |              |              | Specify the name for the VLAG.                             |
| pn_port          | for vlag-create|              |              | Specify the local VLAG port.                               |
| pn_peer_port     | for vlag-create|              |              | Specify the peer VLAG port.                                |
| pn_mode          | no             |              | active-active, active-standby | Specify the VLAG mode.                    |
| pn_peer_switch   | for vlag-create|              |              | Specify the fabric-name of the peer-switch.                |
| pn_failover_action  | no          |              | move, ignore | Specify the failover action as move or ignore.             |
| pn_lacp_mode     | no             |              | off, passive, active | Specify the LACP mode.                             |
| pn_lacp_timeout  | no             |              | slow, fast   | Specify the LACP timeout as slow(30s) or fast(4s).         |
| pn_lacp_fallback | no             |              | individual, bundled | Specify the LACP fallback mode.                     | 
| pn_lacp_fallback_timeout | no     |              |       | The LACP fallback timeout in seconds. Range is between 30s to 60s.|
| pn_quiet         | no             | true         |              | --quiet                                                    |


## Usage

```
- name: "Playbook for CLI VLAG"
  hosts: <hosts>
  user: <user>
  
  tasks:
  - name: "PN VLAG command"
    pn_vlag: >
      pn_cliusername=<username>
      pn_clipassword=<password>
      pn_command=<vlag-create/delete/modify> 
      pn_name=<name>  
      [pn_port=<vlag name>] 
      [pn_peer_port=<peer port>] 
      [pn_mode=<active-active/active-standby>] 
      [pn_peer_switch=<peer switch name>] 
      [pn_failover_action=<move/ignore>] 
      [pn_lacp_mode=<off/passive/active>] 
      [pn_lacp_timeout=<slow/fast>] 
      [pn_lacp_fallback=<individual/bundled>] 
      [pn_fallback_timeout=<timeout>] 
      [pn_quiet=<True/False>]
  
```

## Examples

# cluster-create
Sample playbook for **_creating_** VLAG configuration. 

```
---
- name: Playbook for VLAG Create
  hosts: spine[0]
  user: root
  tasks:
  - name: Create VLAG
    pn_vlag: >
      pn_cliusername=<username>
      pn_clipassword=<password>
      pn_command=vlag-create 
      pn_name=spine-to-leaf1 
      pn_port=spine1-to-leaf1
      pn_peer_switch=spine2
      pn_peer_port=spine2-toleaf1 
      pn_mode=active-active
    register: cmd_output
  - debug: var=cmd_output
  
```

# cluster-delete
Sample playbook for **_deleting_** VLAG configuration.

```
---
- name: Playbook for VLAG Delete
  hosts: spine[0]
  user: root
  tasks:
  - name: Delete VLAGs
    pn_vlag: pn_cliusername=<username> pn_clipassword=<password> pn_command=vlag-delete pn_name=spine-to-leaf1
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
