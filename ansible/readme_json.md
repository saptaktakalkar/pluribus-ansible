

Aim : To have Ansible playbooks’ results in json format with standard output payload
===
---
## Structure:

**The high-level skeleton for json object is:**  
```  
{  
    "plays": [  
        {  
            "play": {  
                "id":   
                "name":  
            },  
            "tasks": [  
                {  
                    "status": {},  
                    "hosts": {},  
                    "task": {  
                        "id":   
                        "name":   
                    }  
                }  
            ]  
        }  
    ]  
}  
```

The standard json object starts with a `plays` field. `plays` field is the highest level field in the json object.  
 
 * `plays` field contains **play** and **tasks** which are next level of field.
   * `play` tells about the description of a play. It contains **name** and **id**  
      * `name` - It gives the name of the `play`  
      * `id` - It gives id of the `play`  
   * `tasks` tells about description of the task in the play. The `tasks` field contains **status**, **hosts** and **task**  
      * `status` tells about the success or failure of the task. It can contain 3 values:  
          * _0_ - for success  
          * _1_ - for failure  
          * _Cannot determine_ - if there is a weird behaviour  
      * `task` field contains task name and task id of the task which is running.  
      * `hosts` field contains the host name where the task execution is happening and host name contains the various attributes for a task which tells about the details on execution of a task in that host.  

### There are 6 fixed attributes inside the hosts field which are:  

`task` - name of task  
`summary` - the json output command by command with the switch name in which it is executing  
`msg` - short message related to the task  
`failed` - true/false depending upon the execution of the task  
`exception` - in case of any exception while running the modules  
`unreachable` - in case of connection issues or some entity is unreachable  

---
## Configuration:

A **json callback plugin** needs to be used to get the desired results in json.  

The name of json plugin is `pn_json.py` which can be found in the locations below:  
1. https://github.com/amitsi/pluribus-ansible/tree/release-2.2.0/ansible  
2. https://github.com/amitsi/pluribus-ansible/tree/master/ansible

Then the `pn_json plugin` needs to be put in the following location:  
1. **/usr/lib/python2.7/dist-packages/ansible/plugins/callback**  

```Note: The plugin needs to be kept in the server machine from where the ansible execution is taking place.```  

Then the following changes have to be added in `/etc/ansible/ansible.cfg` configuration file:  
a) gathering = explicit  
b) stdout\_callback = pn\_json  

---
## Algorithm behind the working:  

* Get the **task name** from `task` field  
*  Then the `status` field has to be checked  
  * if `status` field is ’1’:  
     * Then take the **short error message** from the `msg` field. And **detailed error message** from either `exception/summary/stderr/stdout` field  
   * elif `status` field is '0':  
          * Then take the **short success message** from `msg` field. And the get the **detailed output** from the `summary` field.  
    * else(‘`status`’ field is ‘Cannot determine’):  
      * It is some weird behaviour. Pluribus team to be notified.  

            
