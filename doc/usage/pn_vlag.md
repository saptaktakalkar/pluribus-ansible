# pn_vlag

Execute CLI show commands

| parameter       | required       | default      |choices       |comments                                                    |
|-----------------|----------------|--------------|--------------|------------------------------------------------------------|
|pn_vlagcommand   | yes            |              | vlag-create, vlag-delete, vlag-modify | Create, delete or modify virtual link aggregation|
|pn_vlagname      | yes            |              |              | The VLAG name                                              |
|pn_vlaglport     | conditional    |              |              | The VLAG local port. Required for vlan-create              |
|pn_vlagpeerport  | conditional    |              |              | Description for the vlan. Can be used with vlan-create     |
|pn_vlagmode      | no             |              | active-active, active-standby | The VLAG mode                             |
|pn_vlagpeerswitch| no             |              |              | The VLAG peer switch                                       |
|pn_vlagfailover  | no             |              | failover-move-L2, failover-ignore-L2 | Sends gracious ARPs or not         |
|pn_vlaglacpmode  | no             |              | off, passive, active | The LACP mode                                      |
|pn_vlaglacptimeout| no            |              | slow, fast   | The LACP timeout                                           |
|pn_vlagfallback  | no             |              | individual, bundled | The LACP fallback mode                              | 
|pn_vlagfallbacktimeout | no       | 50           | 30...60 seconds | The LACP fallback timeout                               |
|pn_quiet         | no             | true         |              | --quiet                                                    |

1. [Usage](#usage)
2. [Examples](#examples)

## Usage

```
- name: Playbook for CLI VLAG
  hosts: <hosts>
  user: <user>
  
  tasks:
  - name: PN VLAG command
    pn_vlag: pn_vlagcommand=<vlag-create/delete/modify> pn_vlagname=<name>  [pn_vlaglport] [pn_vlagpeerport] [pn_vlagmode] [pn_vlagpeerswitch] [pn_vlagfailover] [pn_vlaglacpmode] [pn_vlaglacptimeout] [pn_vlagfallback] [pn_vlagfallbacktimeout] pn_quiet=<True/False>
  
```

## Examples

Create VLAGs 
```
---
- name: Playbook for VLAG Create
  hosts: switches
  user: root
  tasks:
  - name: Create VLAG
    pn_vlag: pn_vlagcommand='vlag-create' pn_vlagname={{ item.name }} pn_vlaglport={{ item.self }} pn_vlagpeerport={{ item.peer }} pn_vlagmode='active-active' pn_quiet=True
    with_items: 
    - { name: 'spine-vlag', self: 'spine01', peer: 'spine02' }
    - { name: 'leaf-vlag', self: 'leaf01', peer: 'leaf02' }
    register: cmd_output
  - debug: var=cmd_output
  
```

Delete VLAGs

```
---
- name: Playbook for VLAG Delete
  hosts: switches
  user: root
  tasks:
  - name: Delete VLAGs
    pn_vlag: pn_vlagcommand='vlag-delete' pn_vlagname={{ item }} pn_quiet=True 
    with_items:
    - spine-vlag
    - leaf-vlag
    register: cmd_output
  - debug: var=cmd_output
  
```
