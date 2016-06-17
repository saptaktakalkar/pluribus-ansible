#!/usr/bin/python
# Test PN CLI cluster-delete

DOCUMENTATION = """
---
module: pn_clusterdelete
author: "Pluribus Networks"
short_description: CLI command to delete a cluster.
description:
  - Execute cluster-delete command. Delete a cluster for high availability (HA) in a fabric.
options:
  pn_clustercommand:
    description:
      - The C(pn_clustercommand) takes the cluster-delete command as value.
        Delete a cluster for high availability (HA) in a fabric.
    required: true
    type: str
  pn_clustername:
    description:
      - The C(pn_clustername) takes a valid name for cluster configuration.
        Name of the cluster to be deleted.
    required: true
    type: str
  pn_quiet:
    description:
      - The C(pn_quiet) option to enable or disable the system bootup message.
    required: false
    type: bool
    default: true
"""

EXAMPLES = """
- name: create spine cluster CLI command
  pn_clustercreate: pn_clustercommand='cluster-delete' pn_clustername='spine-cluster' pn_quiet=True
- name: create leaf cluster CLI command
  pn_clustercreate: pn_clustercommand='cluster-delete' pn_clustername='leaf-cluster' pn_quiet=True
"""

RETURN = """
clustercmd:
  description: the CLI command run on the target node(s).
stdout:
  description: the set of responses from the cluster command.
  returned: always
  type: list
stdout_lines:
  description: the value of stdout split into a list.
  returned: always
  type: list
stderr:
  description: the set of error responses from the show command.
  returned: on error
  type: list
"""


import subprocess
import shlex
import json


def main():
	module = AnsibleModule(
		argument_spec = dict(
			pn_clustercommand = dict(required=True, type='str'),
			pn_clustername = dict(required=True, type='str'),
			pn_quiet = dict(default=True, type='bool')
			)
	)

	clustercommand = module.params['pn_clustercommand']
	clustername = module.params['pn_clustername']
	quiet = module.params['pn_quiet']

	if quiet==True:
		cli  = "/usr/bin/cli --quiet "
	else:
		cli = "/usr/bin/cli " 
	
	if clustercommand != "cluster-delete":
		module.fail_json(msg="Invalid command")

	if clustername:
		cluster = cli + clustercommand + ' name ' + clustername

	clustercmd = shlex.split(cluster)

	p = subprocess.Popen(clustercmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
	out,err = p.communicate();


	module.exit_json(
		clustercmd	= cluster,
		stdout	= out.rstrip("\r\n"),
		stderr	= err.rstrip("\r\n"),	
		changed	= True
	)

from ansible.module_utils.basic import *

if __name__ == '__main__':
	main()
