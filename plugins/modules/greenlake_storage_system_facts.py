#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Hewlett Packard Enterprise Development LP.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = '''
---
module: greenlake_storage_system_facts
short_description: Retrieve the facts about storage system
description:
    - Retrieve the facts about one or more of the HPE Greenlake Data Services storage systems
version_added: "2.13.8"
requirements:
    - python >= 3.8
    - greenlake_data_services >= 1.0.0
author: "Sijeesh Kattumunda (@sijeesh)"
options:
    id:
      description:
        - Id of the Greenlake Data Service storage system resource.
      required: false
      type: str
    params:
      description:
        - List of params to delimit, filter and sort the list of resources.
        - "params allowed:
           C(limit): int | Number of items to return at a time (optional)
           C(offset): int | The offset of the first item in the collection to return (optional)
           C(filter): "name eq VEGA_CB1507_8400_2N_150" # str | oData query to filter systems by Key. (optional)
           C(sort): "id asc,name desc" # str | Query to sort the response with specified key and order (optional)
           C(select): "id" # str | Query to select only the required parameters, separated by . if nested (optional)"
      required: false
      type: dict
'''

EXAMPLES = '''
- name: Get GreenLake Data Service storage system resources
  greenlake_storage_system_facts:
    host: <host>
    client_id: <client_id>
    client_secret: <client_secret>
- debug: var=storage_systems
'''

RETURN = '''
storage_systems:
    description: Has all the Greenlake Data Service facts about the storage system resources
    returned: Always, but can be null.
    type: dict
'''

from ansible_collections.hpe.greenlake_data_services.plugins.module_utils.greenlake import GreenLakeDataServiceModule
from greenlake_data_services.api import storage_systems_api


class GreenLakeStorageSystemFactsModule(GreenLakeDataServiceModule):

    def __init__(self):
        argument_spec = dict(id=dict(type='str'),
                             device_type=dict(type='int'),
                             params=dict(type='dict'))

        super(GreenLakeStorageSystemFactsModule, self).__init__(
            additional_arg_spec=argument_spec)

        self.set_resource_client(storage_systems_api.StorageSystemsApi(
            self.greenlake_client))

    def execute_module(self):
        ansible_facts = {'storage_systems': []}

        if self.module.params.get('device_type'):
            device_type = self.module.params['device_type']
            if device_type == 1:
                if self.module.params.get('id'):
                    resp = self.resource_client.device_type1_system_get_by_id(
                        self.module.params['id'])
                    ansible_facts["storage_systems"].append(
                        eval(resp.to_str()))
                else:
                    # Get all Primera / Alletra 9K storage systems
                    resp = self.resource_client.device_type1_systems_list(
                        **self.facts_params)
                    ansible_facts["storage_systems"] = eval(str(resp["items"]))
            else:
                if self.module.params.get('id'):
                    resp = self.resource_client.device_type2_get_storage_system_by_id(
                        self.module.params['id'])
                    ansible_facts["storage_systems"].append(eval(resp.to_str()))
                else:
                    # Get all storage systems by Nimble / Alletra 6K
                    resp = self.resource_client.device_type2_get_storage_system(
                        **self.facts_params)
                    ansible_facts["storage_systems"] = eval(str(resp["items"]))
        else:
            if self.module.params.get('id'):
                resp = self.resource_client.system_get_by_id(
                    self.module.params['id'])
                ansible_facts["storage_systems"].append(resp.to_dict())
            else:
                resp = self.resource_client.systems_list(
                    **self.facts_params)
                ansible_facts["storage_systems"] = resp.to_dict()["items"]

        return dict(changed=False, ansible_facts=ansible_facts)

def main():
    GreenLakeStorageSystemFactsModule().run()


if __name__ == '__main__':
    main()
