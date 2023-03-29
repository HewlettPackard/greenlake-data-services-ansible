#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Hewlett Packard Enterprise Development LP.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = '''
---
module: greenlake_host
short_description: Manage Greenlake Data Service host resources.
description:
    - Provides an interface to manage Greenlake Data Service host resources. Can create, update, and delete.
version_added: "2.13.8"
requirements:
    - python >= 3.8
    - greenlake_data_services >= 1.0.0
author: "Sijeesh Kattumunda (@sijeesh)"
options:
    state:
        description:
            - Indicates the desired state for the Greenlake Data Service host resources.
              C(present) will ensure data properties are compliant with Greenlake Data Service.
              C(absent) will remove the resource from Greenlake Data Service, if it exists.
        choices: ['present', 'absent']
        required: true
        type: str
    data:
        description:
            - List with the Greenlake Data Service host resource properties.
        required: true
        type: dict
'''

EXAMPLES = '''
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

- name: Update GreenLake DSCC Host Name
  greenlake_host:
    host: <host>
    client_id: <client_id>
    client_secret: <client_secret>
    state: present
    data:
      initiator_ids:
        - "b015d393e2274592a37cc7a579c8b0ca"
      name: "hostAnsibleTest"
      operating_system: "Ubuntu"
      user_created: True
      new_name: "hostAnsibleTestUpdated"

- debug: var=hosts

- name: Delete GreenLake DSCC Host
  greenlake_host:
    host: <host>
    client_id: <client_id>
    client_secret: <client_secret>
    state: absent
    data:
      name: "hostAnsibleTestUpdated"
- debug: var=hosts
'''

RETURN = '''
hosts:
    description: Has the facts about Greenlake Data Service host resources
    returned: On state 'present'. Can be null.
    type: dict
'''

from ansible_collections.hpe.greenlake_data_services.plugins.module_utils.greenlake import GreenLakeDataServiceModule, compare
from greenlake_data_services.api import host_initiators_api
from greenlake_data_services.model.create_host_input import CreateHostInput
from greenlake_data_services.model.update_host_input import UpdateHostInput


class GreenLakeDataServiceHostModule(GreenLakeDataServiceModule):

    MSG_CREATED = "Host resource created successfully"
    MSG_DELETED = "Host resource deleted successfully"
    MSG_UPDATED = "Host resource updated"
    MSG_ALREADY_PRESENT = 'Host resource exists with the same details'

    UPDATE_FIELDS = ["initiators_to_create",
                     "name",
                     "updated_initiators"]

    def __init__(self):

        additional_arg_spec = dict(data=dict(required=True, type='dict'),
                                   state=dict(
                                       required=True,
                                       choices=['present', 'absent']))

        super(GreenLakeDataServiceHostModule, self).__init__(
            additional_arg_spec=additional_arg_spec)

        self.set_resource_client(
            host_initiators_api.HostInitiatorsApi(self.greenlake_client))

        self.set_resource_data()

    def get_resource_by_id_or_name(self, id=None, name=None):
        """
         Set resource data by passing id or name
        """
        return self.host_get_by_id_or_name(id, name)

    def execute_module(self):
        changed, msg, ansible_facts = False, '', {}

        if self.state == 'present':
            return self._present()
        elif self.state == 'absent':
            changed, msg, ansible_facts = self._absent()

        return dict(changed=changed, msg=msg, ansible_facts=ansible_facts)

    def _present(self):
        ansible_facts, msg, changed = {"hosts": []}, "", False
        result = {}

        if self.resource_data:
            self.process_input_data(self.UPDATE_FIELDS)

            merged_data = self.resource_data.copy()
            merged_data.update(self.data)

            initiators_to_create = self.data.pop("initiators_to_create", [])
            updated_initiators = self.data.pop("updated_initiators", [])

            initiator_values = [value for initiator in
                                self.resource_data["initiators"]
                                for value in initiator.values()]

            initiators_to_add = [i for i in initiators_to_create
                                 if i.address not in initiator_values]

            initiator_ids_to_update = [i for i in updated_initiators
                                       if i not in initiator_values]

            if (compare(self.resource_data, merged_data)
                    and not initiators_to_add
                    and not initiator_ids_to_update
                    and not self.new_name):
                changed = False
                msg = self.MSG_ALREADY_PRESENT
            else:
                if self.new_name:
                    self.data[self.resource_name_field] = self.new_name

                if initiators_to_add:
                    self.data["initiators_to_create"] = initiators_to_add

                if initiator_ids_to_update:
                    self.data["updated_initiators"] = initiator_ids_to_update

                update_host_input = UpdateHostInput(**self.data)

                api_response = self.resource_client.host_update_by_id(
                    self.resource_data["id"], update_host_input)

                result = self.get_task(api_response.to_dict())
                changed = True
                msg = self.MSG_UPDATED

        else:
            create_host_input = CreateHostInput(**self.data)
            api_response = self.resource_client.host_create(create_host_input)
            result = self.get_task(api_response.to_dict())
            msg = self.MSG_CREATED

        if result and not result.get("error"):
            self.set_resource_data()
            changed = True

        ansible_facts["hosts"].append(self.resource_data)

        return dict(
            msg=msg,
            changed=changed,
            ansible_facts=ansible_facts
        )

    def _absent(self):
        changed = False

        if self.data.get("id") or self.data.get("name"):
            host_id = self.resource_data["id"]

            self.delete_resource(
                "/api/v1/host-initiators/{host_id}?force={force}".format(
                    host_id=host_id, force="true"))

            changed = True
            msg = self.MSG_DELETED
            self.resource_data = {}

        return changed, msg, {}


def main():
    """
    Main method
    """
    GreenLakeDataServiceHostModule().run()


if __name__ == '__main__':
    main()
