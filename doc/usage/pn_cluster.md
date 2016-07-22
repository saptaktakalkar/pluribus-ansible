# pn_cluster

Module for CLI cluster configurations. Supports `cluster-create`, `cluster-delete` and `cluster-modify` commands with options. 

 - [Options](#options)
 - [Usage](#usage)
 - [Examples](#examples)
 - [Return Values](#return-values)

## Options
| parameter       | required       | default      |choices       |comments                                                    |
|-----------------|----------------|--------------|--------------|------------------------------------------------------------|
|pn_cliusername   | yes            |              |              | Login username                                             |
|pn_clipassword   | yes            |              |              | Login password                                             |
|pn_cliswitch     | no             |              |              | Target switch to run command on.
|pn_command       | yes            |              | cluster-create, cluster-delete, cluster-modify | Create, delete or modify cluster configuration|
|pn_name          | yes            |              |              | The Cluster name                                              |
|pn_cluster_node1 | conditional    |              |              | Name for cluster-node-1              |
|pn_cluster_node2 | conditional    |              |              | Name for cluster-node-2     |
|pn_validate      | no             |              |validate, no-validate | Validate the cluster link                            |
|pn_quiet         | no             | true         |              | Enable/disable system information.                           |


## Usage

```
- name: "Playbook for CLI Cluster"
  hosts: <hosts>
  user: <user>
  
  tasks:
  - name: "PN cluster command"
    pn_cluster: > 
     pn_cliusername=<username> 
     pn_clipassword=<password>
     pn_command=<cluster-create/delete/modify> 
     pn_name=<cluster name>  
     [pn_cluster_node1=<cluster-node-1>] 
     [pn_cluster_node2=<cluster-node-2>] 
     [pn_validate=<validate|no-validate>] 
     [pn_quiet=<True/False>]
  
```

## Examples

# cluster-create
YAML Playbook for **_creating_** a Cluster configuration using `pn_cluster` module

```
---
- name: "Playbook for Cluster Create"
  hosts: spine[0]
  user: root
  tasks:
  - name: "Create spine cluster"
    pn_cluster: >
      pn_cliusername=<username> 
      pn_clipassword=<password>
      pn_command=cluster-create 
      pn_name=spine-cluster 
      pn_cluster_node1=spine01 
      pn_cluster_node2=spine02 
      pn_validate=validate 
      pn_quiet=True
    register: cmd_output
  - debug: var=cmd_output
  
```
```
ansible-cm$ ansible-playbook pn_clustercreate.yml -k
```
# cluster-delete
YAML Playbook for **_deleting_** a Cluster Configuration using `pn_cluster` module

```
---
- name: "Playbook for Cluster Delete"
  hosts: spine[0]
  user: root
  tasks:
  - name: "Delete spine cluster"
    pn_cluster:
      pn_cliusername=<username> 
      pn_clipassword=<password>
      pn_command=cluster-delete 
      pn_name=spine-cluster 
      pn_quiet=True
    register: cmd_output
  - debug: var=cmd_output
  
```
## Return Values
| name | description | returned | type |
|--------|------------|----------|---------|
| command | The CLI command run on target nodes| always | string |
| stdout | Output of the CLI command | on success | string |
| stderr | Error message from the CLI command | on failure | string |
| rc | Return code of the CLI command. 0 for success, 1 for failure | always | integer | 
