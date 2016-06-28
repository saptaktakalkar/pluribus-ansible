# pn_cluster

Module for CLI cluster configurations. Supports `cluster-create`, `cluster-delete` and `cluster-modify` commands with options. 

| parameter       | required       | default      |choices       |comments                                                    |
|-----------------|----------------|--------------|--------------|------------------------------------------------------------|
|pn_cliusername  | yes            |              |              | Login username                                              |
|pn_clipassword  | yes            |              |              | Login password                                              |
|pn_clustercommand| yes            |              | cluster-create, cluster-delete, cluster-modify | Create, delete or modify cluster configuration|
|pn_clustername   | yes            |              |              | The Cluster name                                              |
|pn_clusternode1  | conditional    |              |              | Name for cluster-node-1              |
|pn_clusternode2  | conditional    |              |              | Name for cluster-node-2     |
|pn_clustervalidate | no           |              |validate, no-validate | Validate the cluster link                            |
|pn_quiet         | no             | true         |              | --quiet                                                    |


## Usage

```
- name: "Playbook for CLI Cluster"
  hosts: <hosts>
  user: <user>
  
  tasks:
  - name: "PN cluster command"
    pn_cluster: 
     pn_cliusername: <username> 
     pn_clipassword: <password>
     pn_clustercommand: <cluster-create/delete/modify> 
     pn_clustername: <cluster name>  
     [pn_clusternode1: cluster-node-1] 
     [pn_clusternode2: cluster-node-2] 
     [pn_clustervalidate validate|no-validate] 
     pn_quiet: <True/False>
  
```

## Examples

# cluster-create
YAML Playbook for **_creating_** a Cluster configuration using `pn_cluster` module

```
---
- name: "Playbook for Cluster Create"
  hosts: spine
  user: root
  tasks:
  - name: "Create spine cluster"
    pn_cluster: 
      pn_cliusername: <username> 
      pn_clipassword: <password>
      pn_clustercommand: cluster-create 
      pn_clustername: spine-cluster 
      pn_clusternode1: spine01 
      pn_clusternode2: spine02 
      pn_clustervalidate: validate 
      pn_quiet: True
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
  hosts: spine
  user: root
  tasks:
  - name: "Delete spine cluster"
    pn_cluster:
      pn_cliusername: <username> 
      pn_clipassword: <password>
      pn_clustercommand: cluster-delete 
      pn_clustername: spine-cluster 
      pn_quiet: True
    register: cmd_output
  - debug: var=cmd_output
  
```
```
ansible-cm$ ansible-playbook pn_clusterdelete.yml -k
```
