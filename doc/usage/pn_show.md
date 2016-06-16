# pn_show

Execute CLI show commands

| parameter      | required       | default      |choices       |comments                                                    |
|----------------|----------------|--------------|--------------|------------------------------------------------------------|
|pn_showcommand  | yes            |              |vlan-show, vlag-show, cluster-show            |                                                            |
|pn_showoptions  | no             |              |              |                                                            |
|pn_quiet        | no             | True         |              |                                                            |

1. [Usage](#usage)
2. [Examples](#examples)

## Usage

```
- name: Playbook for VLAN CLI show
  hosts: <hosts>
  user: <user>
  
  tasks:
  - name: PN CLI SHOW command
    pn_show: pn_showcommand=<CLI show command> pn_showoptions='format <options>' pn_quiet=<True/False>
  
```

## Examples

View VLAN configurations of a given host(s)
```
---
- name: PN-CLI VLAN Show Test
  hosts: testswitches
  user: root
  tasks:
  - name: Test VLAN Show CLI command
    pn_show: pn_showcommand='vlan-show' pn_showoptions='format switch,id,scope,description' pn_quiet=True 
    register: cmd_output
  - debug: var=cmd_output
  
```

View cluster configurations
```
---
- name: PN-CLI Cluster Show Test
  hosts: testswitches
  user: root
  tasks:
  - name: Test cluster Show CLI command
    pn_show: pn_showcommand='cluster-show' pn_quiet=True 
    register: cmd_output
  - debug: var=cmd_output
  
```
