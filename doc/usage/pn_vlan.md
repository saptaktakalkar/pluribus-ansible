# pn_vlan

Execute CLI show commands

| parameter      | required       | default      |choices       |comments                                                    |
|----------------|----------------|--------------|--------------|------------------------------------------------------------|
|pn_vlancommand  | yes            |              | vlan-create, vlan-delete            |                                                            |
|pn_vlanid       | yes            |              |              | Range: 2 - 4092                                               |
|pn_vlanscope    | conditional    |              | fabric, local| Required for vlan-create                                                      |
|pn_vlandesc     | no             |              |              | Description for the vlan. Can be used with vlan-create.   |
|pn_vlanstats    | no             |              | stats, no-stats| Enable/disable stats for the vlan. Can be used with vlan-create.  |
|pn_vlanports    | no             |              | | Comma separated list of ports for the vlan. Can be used with vlan-create.  |
|pn_vlanuntaggedports    | no             |              | | Comma separated list of untagged ports for the vlan. Can be used with vlan-create.  |
|pn_quiet        | no             | true         |              | --quiet                                                       |

1. [Usage](#usage)
2. [Examples](#examples)

## Usage

```
- name: Playbook for CLI VLAN
  hosts: <hosts>
  user: <user>
  
  tasks:
  - name: PN VLAN command
    pn_vlan: pn_vlancommand=<vlan-create/vlan-delete> pn_vlaid=<vlan-id> [pn_vlanscope=<fabric/local>] [pn_vlandesc=<desc>] [pn_vlanstats=<stats/no-stats] [pn_vlanports=<comma separated ports-list>] [pn_vlanuntaggedports=<comma separated untagged ports-list>] pn_quiet=<True/False>
  
```

## Examples

Create VLAN with id = 254 and scope = local
```
---
- name: Playbook for VLAN Create
  hosts: spine
  user: root
  tasks:
  - name: Create VLAN
    pn_vlan: pn_vlancommand='vlan-create' pn_vlanid=254 pn_vlanscope='local' pn_vlandesc='ansible-vlan' pn_quiet=True 
    register: cmd_output
  - debug: var=cmd_output
  
```

Create 3 VLANs with different IDs and scope
```
---
- name: Playbook for VLAN Create
  hosts: spine
  user: root
  tasks:
  - name: Create VLANs 
    pn_vlan: pn_vlancommand='vlan-create' pn_vlanid={{ item.id }} pn_vlanscope={{ item.scope }} pn_quiet=True 
    with_items:
    - { id: '201', scope: 'fabric' }
    - { id: '1024', scope: 'local' }
    - { id: '355', scope: 'fabric' }
    register: cmd_output
  - debug: var=cmd_output
  
```
Delete all the created VLANs

```
---
- name: Playbook for VLAN Delete
  hosts: spine
  user: root
  tasks:
  - name: Delete VLANs
    pn_vlan: pn_vlancommand='vlan-delete' pn_vlanid={{ item }} pn_quiet=True 
    with_items:
    - 254
    - 201
    - 1024
    - 355
    register: cmd_output
  - debug: var=cmd_output
  
```
