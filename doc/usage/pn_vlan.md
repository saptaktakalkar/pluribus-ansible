# pn_vlan

Module for CLI vlan configurations. Supports `vlan-create` or `vlan-delete` commands with options. 

| parameter      | required       | default      |choices       |comments                                                    |
|----------------|----------------|--------------|--------------|------------------------------------------------------------|
|pn_cliusername  | yes            |              |              | Login username                                             |
|pn_clipassword  | yes            |              |              | Login password                                             |
|pn_cliswitch    | no             |              |              | Target switch to run the CLI on.                           |
|pn_command  | yes            |              | vlan-create, vlan-delete | Create or Delete VLAN configuration                                                            |
|pn_vlanid       | yes            |              |              | Range: 2 - 4092                                               |
|pn_scope    | if vlan-create    |              | fabric, local| Scope. Required for vlan-create                                                      |
|pn_description     | no             |              |              | Description for the vlan. Required for vlan-modify    |
|pn_stats    | no             |              | stats, no-stats| Enable/disable stats for the vlan  |
|pn_ports    | no             |              | | Comma separated list of ports for the vlan |
|pn_untaggedports    | no             |              | | Comma separated list of untagged ports for the vlan  |
|pn_quiet        | no             | true         |              | --quiet                                                       |

1. [Usage](#usage)
2. [Examples](#examples)

## Usage

```
- name: "Playbook for CLI VLAN"
  hosts: <hosts>
  user: <user>

  tasks:
  - name: PN VLAN command
    pn_vlan: pn_cliusername=<username> pn_clipassword=<password> pn_command=<vlan-create/vlan-delete> pn_vlanid=<vlan-id> [pn_scope=<fabric/local>] [pn_description=<desc>] [pn_stats=<stats/no-stats] [pn_ports=<comma separated ports-list>] [pn_untaggedports=<comma separated untagged ports-list>] pn_quiet=<True/False>
  
```

## Examples


# vlan-create
YAML Playbook for **_creating_** a vlan configuration using `pn_vlan` module
```
---
- name: Playbook for VLAN Create
  hosts: spine[0]
  user: root
  tasks:
  - name: Create VLAN
    pn_vlan: pn_cliusername=<username> pn_clipassword=<password> pn_command=vlan-create pn_vlanid=254 pn_scope=fabric 
    register: cmd_output
  - debug: var=cmd_output
  
```

YAML Playbook for **_creating_** multiple vlan configurations using `pn_vlan` module
```
---
- name: Playbook for VLAN Create
  hosts: spine[0]
  user: root
  tasks:
  - name: Create VLANs 
    pn_vlan: pn_cliusername=<username> pn_clipassword=<password> pn_command=vlan-create pn_vlanid={{ item }} pn_scope=fabric 
    with_sequence: start=300 end=305
    register: cmd_output
  - debug: var=cmd_output
  
```
# vlan-delete
YAML Playbook for **_deleting_** a vlan configuration using `pn_vlan` module

```
---
- name: Playbook for VLAN Delete
  hosts: spine[0]
  user: root
  tasks:
  - name: Delete VLANs
    pn_vlan: pn_cliusername=<username> pn_clipassword=<password> pn_command=vlan-delete pn_vlanid=254
    register: cmd_output
  - debug: var=cmd_output
  
```
