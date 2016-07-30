#!/usr/bin/python
""" This is a basic module to run any PN CLI commands. 
    The CLI command should be provide to 'pn_command' parameter.
"""

import subprocess
import shlex


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=True, type='str'),
            pn_clipassword=dict(required=True, type='str'),
            pn_cliswitch=dict(required=False, type='str'),
            pn_command=dict(required=True, type='str'),
            pn_quiet=dict(default=True, type='bool')
        )
    )

    cliusername = module.params['pn_cliusername']
    clipassword = module.params['pn_clipassword']
    cliswitch = module.params['pn_cliswitch']
    command = module.params['pn_command']
    quiet = module.params['pn_quiet']

    # Building the CLI command string
    cli = '/usr/bin/cli'
    
    if quiet is True:
        cli += ' --quiet '
    
    cli += ' --user %s:%s ' % (cliusername, clipassword)
    
    if cliswitch:
        cli += ' switch-local ' if cliswitch == 'local' else ' switch ' + cliswitch
    
    cli += ' ' + command

    cli_command = shlex.split(cli)
    response = subprocess.Popen(cli_command, stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE, universal_newlines=True)

    # 'out' contains the output
    # 'err' contains the error messages
    out, err = response.communicate()

    # Response in JSON format
    if err:
        module.exit_json(
            command=cli,
            stderr=err.rstrip("\r\n"),
            changed=False
        )

    else:
        module.exit_json(
            command=cli,
            stdout=out.rstrip("\r\n"),
            changed=True
        )

# AnsibleModule boilerplate
from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()
