## Setup Ansible Config

Update the following in /etc/ansible/ansible.cfg to appropriate location:

```
library        = /etc/ansible/pluribus-ansible/ansible/library
```

And also uncomment the following:

```
host_key_checking = False
```

## Run playbooks

### Switch-Config-Reset Playbook

Playbook command:

```
# ansible-playbook -i hosts pn_switch_reset.yml -u pluribus --ask-pass --ask-vault-pass -K
```

Output snippet:

```
--snip--
PLAY [Switch Config Reset] *****************************************************

TASK [setup] *******************************************************************
ok: [ansible-leaf2]
ok: [ansible-leaf3]
ok: [ansible-leaf1]
ok: [ansible-spine2]
ok: [ansible-spine1]
ok: [ansible-leaf4]

TASK [Reset all switches] ******************************************************
ok: [ansible-leaf3]
ok: [ansible-leaf2]
ok: [ansible-leaf1]
ok: [ansible-spine1]
ok: [ansible-spine2]
ok: [ansible-leaf4]
.
.
PLAY RECAP *********************************************************************
ansible-leaf1              : ok=3    changed=0    unreachable=0    failed=0
ansible-leaf2              : ok=3    changed=0    unreachable=0    failed=0
ansible-leaf3              : ok=3    changed=0    unreachable=0    failed=0
ansible-leaf4              : ok=3    changed=0    unreachable=0    failed=0
ansible-spine1             : ok=4    changed=0    unreachable=0    failed=0
ansible-spine2             : ok=3    changed=0    unreachable=0    failed=0
--snip--
```

### Fabric Playbook

Playbook command:

```
# ansible-playbook -i hosts pn_fabric.yml -u pluribus --ask-pass --ask-vault-pass -K
```

Output snippet:

```
--snip--
PLAY [Zero Touch Provisioning - Initial setup] *********************************

TASK [setup] *******************************************************************
ok: [ansible-spine1]

TASK [Auto accept EULA, Disable STP, enable ports and create/join fabric] ******
changed: [ansible-spine1]

TASK [debug] *******************************************************************
ok: [ansible-spine1] => {
    "ztp_out.stdout_lines": [
        "  EULA has been accepted already!  ansible-spine1 is already in fabric vcf-ansible-fab!  Fabric is already in mgmt control network  STP is already disabled!  Ports enabled on ansible-spine1! "
    ]
}
.
.
PLAY RECAP *********************************************************************
ansible-leaf1              : ok=4    changed=1    unreachable=0    failed=0
ansible-leaf2              : ok=4    changed=1    unreachable=0    failed=0
ansible-leaf3              : ok=4    changed=1    unreachable=0    failed=0
ansible-leaf4              : ok=4    changed=1    unreachable=0    failed=0
ansible-spine1             : ok=4    changed=1    unreachable=0    failed=0
ansible-spine2             : ok=4    changed=1    unreachable=0    failed=0
--snip--
```

### Fabric Playbook - L2 with VRRP

Create a CSV file. Sample CSV file:
```
# cat pn_vrrp_l2.csv
101.108.100.0/24, 100, test-spine1
101.108.101.0/24, 101, test-spine1
101.108.102.0/24, 102, test-spine2
101.108.103.0/24, 103, test-spine2
```

Modify CSV file path in YML file:

```
  vars:
  - csv_file: /pluribus-ansible/ansible/pn_vrrp_l2.csv  # CSV file path.
```

Playbook command:

```
# ansible-playbook -i hosts pn_vrrp_l2_with_csv.yml -u pluribus --ask-pass --ask-vault-pass -K
```

### Fabric Playbook - L3

Playbook command:

```
# ansible-playbook -i hosts pn_l3_ztp.yml -u pluribus --ask-pass --ask-vault-pass -K
```

### Fabric Playbook - L3 with VRRP

Create a CSV file. Sample CSV file:

```
# cat pn_vrrp_l3.csv
100, 172.168.100.0/24, test-leaf1, test-leaf2, 19, test-leaf1
101, 172.168.101.0/24, test-leaf3
102, 172.168.102.0/24, test-leaf4
104, 172.168.104.0/24, test-leaf1, test-leaf2, 19, test-leaf1
```

Modify CSV file path in YML file:

```
  vars:
  - csv_file: /etc/ansible/pluribus-ansible/ansible/pn_vrrp_l3.csv  # CSV file path.
```

Playbook command:

```
# ansible-playbook -i hosts pn_vrrp_l2_with_csv.yml -u pluribus --ask-pass --ask-vault-pass -K
```


