# Ansible Collection for HPE Greenlake Data Services

This collection provides a series of Ansible modules and plugins for interacting with the HPE Greenlake Data Services.

## Requirements

 - Ansible >= 2.9
 - python >= 3.8
 - [HPE Greenlake Data Service Python SDK](https://github.com/HewlettPackard/greenlake-data-services-python)

# Installation
To install HPE Greenlake Data Service collection hosted in Galaxy (Currently not available)

```bash
ansible-galaxy collection install hpe.greenlake_data_services
```

To upgrade to the latest version of HPE  Greenlake Data Service collection:

```bash
ansible-galaxy collection install hpe.greenlake_data_services --force
```

To install HPE Greenlake Data Service collection from GitHub
```bash
git clone https://github.com/HewlettPackard/greenlake-data-services-ansible
cd greenlake-data-services-ansible
ansible-galaxy collection build .
```
Now a tar file is generated. Install that file.
```
ansible-galaxy collection install <tar_file>
```

To install dependency packages

```bash
pip install -r requirements.txt
```

###  HPE Greenlake Data Services Configuration

#### Using a JSON Configuration File

To use the HPE Greenlake Data Services collection, you can store the configuration in a JSON file.
Here's an example:

```json
{
  "host": "<host>",
  "client_id": "<client_id>",
  "client_secret": "<client_secret>"
}
```

Once you have defined the config variables, you can run the roles.

#### Parameters in roles

The another way is to pass the credentials through explicit specification on the task.

This option allows the parameters `host`, `client_id`, `client_secret` to be passed directly inside your task.

```yaml
- name: Create GreenLake DSCC Host
  greenlake_host:
    host: <host>
    client_id: <client_id>
    client_secret: <client_secret>
    state: present
    data:
      initiator_ids:
        - "f582f56aa7b24964aca9b08496d7e378"
      name: "hostAnsibleTest"
      operating_system: "Ubuntu"
      user_created: True
- debug: var=hosts
```

### Usage

Playbooks

To use a module from HPE Greenlake Data Services collection, please reference the full namespace, collection name, and modules name that you want to use:

```bash
---
- name: Using HPE Greenlake Data Services collection
- hosts: all
  collections:
    - hpe.greenlake_data_services
  roles:
    - role: hpe.greenlake_data_services.host_facts
```

## License

This project is licensed under the GNU General Public License v3.0. Please see the [LICENSE](LICENSE) for more information.

## Contributing and feature requests

**Contributing:** We welcome your contributions to the Ansible Modules for HPE Greenlake Data Services. See [CONTRIBUTING.md](CONTRIBUTING.md) for more details.

**Feature Requests:** If you have a need that is not met by the current implementation, please let us know (via a new issue).
This feedback is crucial for us to deliver a useful product. Do not assume that we have already thought of everything, because we assure you that is not the case.

## Features

The HPE Greenlake Data Services collection includes
[roles](https://github.com/HewlettPackard/greenlake-data-services-ansible/tree/master/roles/),
[modules](https://github.com/HewlettPackard/greenlake-data-services-ansible/tree/master/plugins/modules),
[module_utils](https://github.com/HewlettPackard/greenlake-data-services-ansible/tree/master/plugins/module_utils)


## Copyright

© Copyright 2023 Hewlett Packard Enterprise Development LP
