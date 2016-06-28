#!/usr/bin/python
# Test PN CLI vrouter-loopback-interface-add/remove/modify


DOCUMENTATION = """
---
module: pn_cluster
author: "Pluribus Networks"
short_description: CLI command to create/delete a cluster
description:
  - Execute cluster-create or cluster-delete command. 
  - Requires cluster name:
  	- Alphanumeric characters
  	- Special characters like: _ 
options:
  pn_clustercommand:
    description:
      - The C(pn_clustercommand) takes the cluster-create/cluster-delete command as value.
    required: true
    choices: cluster-create, cluster-delete
    type: str
  pn_clustername:
    description:
      - The C(pn_clustername) takes a valid name for cluster configuration.
    required: true
    type: str
  pn_clusternode1:
    description:
      - name for cluster-node 1
    required_if: cluster-create 
    type: str
  pn_clusternode2:
    description:
      - name for cluster-node 2
    required_if: cluster-create
    type: str
  pn_clustervalidate:
    description:
      - validate the cluster link
    required: false
    choices: validate, no-validate
    type: str
  pn_quiet:
    description:
      - The C(pn_quiet) option to enable or disable the system bootup message
    required: false
    type: bool
    default: true
"""

EXAMPLES = """
- name: create spine cluster 
  pn_cluster: pn_clustercommand='cluster-create' pn_clustername='spine-cluster' pn_clusternode1='spine01' pn_clusternode2='spine02' pn_clustervalidate=True pn_quiet=True
- name: delete spine cluster 
  pn_cluster: pn_clustercommand='cluster-delete' pn_clustername='spine-cluster' pn_quiet=True
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
  description: the set of error responses from the cluster command.
  returned: on error
  type: list
"""
import subprocess
import shlex
import json


def main():
        module = AnsibleModule(
                argument_spec = dict(
                        pn_vrouterlbcommand = dict(required=True, type='str', choices=['vrouter-create', 'vrouter-delete', 'vrouter-modify']),
                        pn_vrouterlbname = dict(required=True, type='str'),
                        pn_vrouterlbindex = dict(required=False, type='int'),
                        pn_vrouterlbip = dict(required=False, type='str'), 
			pn_quiet = dict(default=True, type='bool')
                        ),
                required_if = (
                        [ "pn_vrouterlbcommand", "vrouter-loopback-interface-add", ["pn_vrouterlbname", "pn_vrouterlbindex", "pn_vrouterlbip"] ],
                        [ "pn_vrouterlbcommand", "vrouter-loopback-interface-remove", ["pn_vrouterlbname", "pn_vrouterlbindex"] ],
			[ "pn_vrouterlbcommand", "vrouter-loopback-interface-modify", ["pn_vrouterlbname"]]
                        ),
		supports_check_mode = True
        )

        vrouterlbcommand = module.params['pn_vrouterlbcommand']
        vrouterlbname = module.params['pn_vrouterlbname']
        vrouterlbindex = module.params['pn_vrouterlbindex']
        vrouterlbip = module.params['pn_vrouterlbip']
        quiet = module.params['pn_quiet']

        if quiet==True:
                cli  = "/usr/bin/cli --quiet "
        else:
                cli = "/usr/bin/cli "


        if vrouterlbname:
                vrouterlb = cli + vrouterlbcommand + ' vrouter-name ' + vrouterlbname

        if vrouterlbindex:
                vrouterlb += ' index ' + str(vrouterlbindex)

        if vrouterlbip:
		vrouterlb += ' ip ' + vrouterlbip

        vrouterlbcmd = shlex.split(vrouterlb)

        p = subprocess.Popen(vrouterlbcmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
        out,err = p.communicate();


        module.exit_json(
                vrouterlbcmd = vrouterlb,
                stdout = out.rstrip("\r\n"),
                stderr = err.rstrip("\r\n")
#                changed = True
        )

from ansible.module_utils.basic import *

if __name__ == '__main__':
        main()
