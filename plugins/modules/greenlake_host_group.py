#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Hewlett Packard Enterprise Development LP.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = '''
---
module: greenlake_host_group
short_description: Manage Greenlake Data Service host group resources.
description:
    - Provides an interface to manage Greenlake Data Service host group resources. Can create, update, and delete.
version_added: "2.13.8"
requirements:
    - python >= 3.8
    - greenlake_data_services >= 1.0.0
author: "Sijeesh Kattumunda (@sijeesh)"
options:
    state:
        description:
            - Indicates the desired state for the Greenlake Data Service host group resources.
              C(present) will ensure data properties are compliant with Greenlake Data Service.
              C(absent) will remove the resource from Greenlake Data Service, if it exists.
        choices: ['present', 'absent']
        required: true
        type: str
    data:
        description:
            - List with the Greenlake Data Service host group resource properties.
        required: true
        type: dict
'''

EXAMPLES = '''
- name: Create GreenLake DSCC Host Group
  greenlake_host_group:
    host: <host>
    client_id: <client_id>
    client_secret: <client_secret>
    state: present
    data:
      name: "<resource_name>"
      hostIds: "<host_ids>"
      user_created: True

- debug: var=host_groups

- name: Update name of GreenLake DSCC Host Group
  greenlake_host_group
    host: <host>
    client_id: <client_id>
    client_secret: <client_secret>
    state: present
    data:
      name: "<resource_name>"
      new_name: "<resource_name_updated>"
      updated_hosts: "<update_host_ids>"
      user_created: True
- debug: var=host_groups

- name: Delete GreenLake DSCC Host Group
  greenlake_host_group:
    host: <host>
    client_id: <client_id>
    client_secret: <client_secret>
    state: absent
    data:
      name: "<resource_name_updated>"
      force: True
'''

RETURN = '''
greenlake_host_group:
    description: Has the facts about Greenlake Data Service host group resources
    returned: On state 'present'. Can be null.
    type: dict
'''

from ansible_collections.hpe.greenlake_data_services.plugins.module_utils.greenlake import GreenLakeDataServiceModule, compare

from greenlake_data_services.api import host_initiator_groups_api
from greenlake_data_services.model.create_host_group_input import CreateHostGroupInput
from greenlake_data_services.model.update_host_group_input import UpdateHostGroupInput


class GreenLakeDataServiceHostGroupModule(GreenLakeDataServiceModule):

    MSG_CREATED = "Host Group resource created successfully"
    MSG_DELETED = "Host Group resource deleted successfully"
    MSG_UPDATED = "Host Group resource updated successfully"
    MSG_ALREADY_PRESENT = ("Host Group resource exists with the"
                           "same configuration")

    UPDATE_FIELDS = ["hosts_to_create",
                     "name",
                     "updated_hosts"]

    def __init__(self):

        additional_arg_spec = dict(data=dict(required=True, type='dict'),
                                   state=dict(
                                       required=True,
                                       choices=['present', 'absent']))

        super(GreenLakeDataServiceHostGroupModule, self).__init__(
            additional_arg_spec=additional_arg_spec)

        # Set Host Group resource client
        self.set_resource_client(
            host_initiator_groups_api.HostInitiatorGroupsApi(
                self.greenlake_client))

        # Set resource data if a resource exists with the same name/id passed
        self.set_resource_data()

    def get_resource_by_id_or_name(self, id=None, name=None):
        """
         Set resource data by passing id or name
        """
        return self.host_group_get_by_id_or_name(id, name)

    def execute_module(self):
        changed, msg, ansible_facts = False, '', {}

        if self.state == 'present':
            return self._present()
        elif self.state == 'absent':
            changed, msg, ansible_facts = self._absent()

        return dict(changed=changed, msg=msg, ansible_facts=ansible_facts)

    def _present(self):
        """
        Handles create/update operations
        """
        ansible_facts, msg, changed = {"host_groups": []}, "", False
        result = {}

        if self.resource_data:
            self.process_input_data(self.UPDATE_FIELDS)
            merged_data = self.resource_data.copy()
            merged_data.update(self.data)

            # Not supporting now to avoid passing complex input data
            # TODO: If required, support can be added in the future
            self.data.pop("hosts_to_create", [])

            updated_hosts = self.data.pop("updated_hosts", [])
            host_values = [value for host in
                           self.resource_data["hosts"]
                           for value in host.values()]

            host_ids_to_update = [i for i in updated_hosts
                                  if i not in host_values]

            if (compare(self.resource_data, merged_data)
                    and not host_ids_to_update
                    and not self.new_name):
                changed = False
                msg = self.MSG_ALREADY_PRESENT
            else:
                if self.new_name:
                    self.data[self.resource_name_field] = self.new_name

                if host_ids_to_update:
                    self.data["updated_hosts"] = host_ids_to_update

                update_host_group_input = UpdateHostGroupInput(**self.data)

                api_response = self.resource_client.host_group_update_by_id(
                    self.resource_data["id"],
                    update_host_group_input)

                result = self.get_task(api_response.to_dict())
                changed = True
                msg = self.MSG_UPDATED

        else:
            create_host_group_input = CreateHostGroupInput(**self.data)

            api_response = self.resource_client.host_group_create(
                create_host_group_input)

            result = self.get_task(api_response.to_dict())
            msg = self.MSG_CREATED

        if result and not result.get("error"):
            self.set_resource_data()
            changed = True

        ansible_facts["host_groups"].append(self.resource_data)

        return dict(
            msg=msg,
            changed=changed,
            ansible_facts=ansible_facts
        )

    def _absent(self):
        changed = False

        if self.data.get("id") or self.data.get("name"):
            host_group_id = self.resource_data["id"]

            self.delete_resource(
                "/api/v1/host-initiator-groups/{host_group_id}?force={force}"
                .format(host_group_id=host_group_id, force="true"))

            changed = True
            msg = self.MSG_DELETED
            self.resource_data = {}

        return changed, msg, {}


def main():
    """
    Main method
    """
    GreenLakeDataServiceHostGroupModule().run()


if __name__ == '__main__':
    main()
