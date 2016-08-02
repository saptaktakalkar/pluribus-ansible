# pn_vrouter

Module for CLI vrouter configurations. Supports `vrouter-create`, `vrouter-delete` and `vrouter-modify` commands with options.

| parameter      | required       | default      |choices       |comments                                                    |
|----------------|----------------|--------------|--------------|------------------------------------------------------------|
|pn_cliusername  | yes            |              |              | Login username                                             |
|pn_clipassword  | yes            |              |              | Login password                                             |
|pn_vroutercommand | yes          |              | vrouter-create, vrouter-delete, vrouter-modify | Create, delete, modify vrouter configurations|
|pn_vroutername    | yes          |              |              | Name for the configuration                                               |
|pn_vroutervnet    | conditional  |              | | VNET assigned to the service. Required for vrouter-create                                                      |
|pn_vrouterstate   | conditional  |              | enable, disable| State of the service. Required for vrouter-create |
|pn_vrouterhw_vrrp_id| conditional|              | | VRRP id assigned to the hardware router. Required for vrouter-create|
|pn_vrouterbgp_as  | no           |              | | BGP Autonomous System number from 1 to 4294967295  |
|pn_quiet        | no             | true         |              | --quiet                                                       |


## Usage

```
- name: "Playbook for CLI vrouter"
  hosts: <hosts>
  user: <user>
  
  tasks:
  - name: "PN vrouter command"
    pn_vlan: pn_cliusername=<username> pn_clipassword=<password> pn_vroutercommand=<vrouter-create/delete/modify> pn_vroutername=<name> [pn_vroutervnet] [pn_vrouterstate] [pn_vrouterhw_vrrp_id] [pn_vrouterbgp_as] pn_quiet=<True/False>
  
```

## Examples

# vrouter-create
YAML Playbook for **_creating_** a vrouter configuration using `pn_vrouter` module
```
---
- name: "Playbook for vrouter Create"
  hosts: switches
  user: root
  tasks:
  - name: "Create vrouter"
    pn_vrouter: pn_cliusername=<username> pn_clipassword=<password> pn_routercommand='vrouter-create' pn_vroutername='ansible-vrouter' pn_vroutervnet='ansible-vnet' pn_vrouterstate='enable' pn_vrouterhw_vrrp_id=18 pn_quiet=True
    register: cmd_output
  - debug: var=cmd_output
  
```

# vrouter-delete
YAML Playbook for **_deleting_** a vrouter configuration using `pn_vrouter` module

```
---
- name: "Playbook for vrouter Delete"
  hosts: switches
  user: root
  tasks:
  - name: "Delete vrouter"
    pn_vrouter: pn_cliusername=<username> pn_clipassword=<password> pn_vroutercommand='vrouter-delete' pn_vroutername='ansible-vrouter' pn_quiet=True
    register: cmd_output
  - debug: var=cmd_output
  
```
