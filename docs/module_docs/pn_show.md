# pn_show

Execute CLI show commands.

 - [Synopsis](#synopsis)
 - [Options](#options)
 - [Usage](#usage)
 - [Examples](#examples)
 - [Return Values](#return-values)
 
## Synopsis

  This module is used to execute CLI show commands to gather configuration information. You can specify the parameter list you want to view, provide different formating options such as sort, no-show-headers among others.
  For a complete discussion of all the features, please refer to the Pluribus Networks technical product documentation.

## Options

| parameter      | required       | default      | type        |choices        |comments                                      |
|----------------|----------------|--------------|-------------|---------------|----------------------------------------------|
| pn_cliusername | see comments   |              | str         |               | Provide login username if user is not root.  |
| pn_clipassword | see comments   |              | str         |               | Provide login password if user is not root.  |
| pn_cliswitch   | no             |              | str         |               | Target switch(es) to run command on.         |
| pn_command     | yes            |              | str         | vlan-show, vlag-show, cluster-show...| CLI Show commands     |
| pn_parameters  | no             | all          | str         |               |  Display output using a specific parameter. Use 'all' to display possible output. List of comman separated parameters.|
| pn_options     | no             |              | str         |               | Specify formatting options.                  |


## Usage

```
- name: Playbook for CLI show
  hosts: <hosts>
  user: <user>
  
  vars_files:
  - foo_vault.yml
  
  tasks:
  - name: PN CLI SHOW command
    pn_show: 
      [pn_cliusername: <username>] 
      [pn_clipassword: <password>] 
      pn_command: <CLI show command> 
      [pn_parameters: <parameters>]
      [pn_options: <options>]
    - debug
  
```

## Examples

View VLAN configurations of a given host(s)

Equivalent CLI:
```
CLI......> vlan-show format switch,id,scope,description no-show-headers
```

```
---
- name: PN-CLI VLAN Show Test
  hosts: spine[0]
  user: pluribus
  
  vars_files:
  - foo_vault.yml
  
  tasks:

  - name: Test VLAN Show CLI command
    pn_show: 
      pn_cliusername: "{{ USERNAME }}" 
      pn_clipassword: "{{ PASSWORD }}"
      pn_command: vlan-show 
      pn_parameters: 'switch,id,scope,description'
      pn_options: no-show-headers
    register: cmd_output
  - debug: var=cmd_output
  
```

View cluster configurations

Equivalent CLI:
```
CLI......> cluster-show name spine-cluster
```

```
---
- name: PN-CLI Cluster Show Test
  hosts: spine[0]
  user: root
  
  
  tasks:
  - name: Test cluster Show CLI command
    pn_show: 
      pn_showcommand: cluster-show
      pn_options: 'name spine-cluster'
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
