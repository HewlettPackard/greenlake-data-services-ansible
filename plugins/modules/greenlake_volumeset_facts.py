#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Hewlett Packard Enterprise Development LP.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = '''
---
module: greenlake_volumeset_facts
short_description: Retrieve the facts about volumeset resources
description:
    - Retrieve the facts about one or more of the HPE Greenlake Data Services volumeset resources
version_added: "2.4.0"
requirements:
    - python >= 3.8
    - greenlake_data_services >= 1.0.0
author: "Sijeesh Kattumunda (@sijeesh)"
options:
    id:
      description:
        - Id of the Greenlake Data Service volumeset resource.
      required: false
      type: str
    name:
      description:
        - Name of the Greenlake Data Service volumeset resource.
      required: false
      type: str
    options:
      description:
        - "List with options to gather additional facts about Greenlake Data Service volumeset resources.
          Options allowed:
          getVolumes get list of volumes
          getSnapshots get lsit of snapshots
        - "To gather facts about getVolumes and getSnapshots
           a Volumeset name/id is required. Otherwise, these options will be ignored."
      type: list
    params:
      description:
        - List of params to delimit, filter and sort the list of resources.
        - "params allowed:
           C(limit): int | Number of items to return at a time (optional)
           C(offset): int | The offset of the first item in the collection to return (optional)
           C(filter): "name eq volset and systemId eq 7CE751P312" # str | oData query to filter by Key. (optional)
           C(sort): "systemId desc" # str | oData query to sort by Key. (optional)
           C(select): "id" # str | Query to select only the required parameters, separated by . if nested (optional)
      required: false
      type: dict
'''

EXAMPLES = '''
- name: Get GreenLake Data Service volumeset resources
  greenlake_volumeset_facts:
    host: <host>
    client_id: <client_id>
    client_secret: <client_secret>
- debug: var=volume_sets
'''

RETURN = '''
volume_sets:
    description: Has all the Greenlake Data Service facts about the volumeset resources.
    returned: Always, but can be null.
    type: dict
'''

from greenlake_data_services.api import volume_sets_api
from ansible_collections.hpe.greenlake_data_services.plugins.module_utils.greenlake import GreenLakeDataServiceModule


class GreenLakeVolumeSetFactsModule(GreenLakeDataServiceModule):

    def __init__(self):
        argument_spec = dict(id=dict(type='str'),
                             name=dict(type='str'),
                             system_id=dict(type='str'),
                             device_type=dict(required=True,
                                              choices=['1', '2']),
                             options=dict(type='list'),
                             params=dict(type='dict'))

        super(GreenLakeVolumeSetFactsModule, self).__init__(
            additional_arg_spec=argument_spec)

        self.set_resource_client(volume_sets_api.VolumeSetsApi(
            self.greenlake_client))

        self.set_resource_data()

    def get_resource_by_id_or_name(self, id=None, name=None):
        """
         Set resource data by passing id or name
        """
        return self.volume_set_get_by_id_or_name(self.system_id, id, name)

    def execute_module(self):
        ansible_facts = {'volume_sets': []}

        if self.module.params.get('id') or self.module.params.get('name'):
            ansible_facts["volume_sets"].append(self.resource_data)

            if self.options:
                more_facts = self.__gather_optional_facts(ansible_facts)
                ansible_facts.update(more_facts)

        elif self.module.params.get('system_id'):
            api_response = self.resource_client.device_type1_volume_sets_list(
                self.module.params['system_id'])

            ansible_facts["volume_sets"] = api_response.to_dict()["items"]

        else:
            api_response = self.resource_client.volumeset_list(
                **self.facts_params)

            ansible_facts["volume_sets"] = api_response.to_dict()["items"]

        return dict(changed=False, ansible_facts=ansible_facts)

    def __gather_optional_facts(self, ansible_facts):
        more_facts = {"snapshots": [], "volumes": []}

        if self.options.get('getVolumes'):
            api_response = self.resource_client.volumeset_get_byvolumeset_id(
               self.resource_data['id'])
            response = api_response.to_dict()
            if response.get("items"):
                more_facts["volumes"] = response["items"]

        if self.options.get('getSnapshots'):
            api_response = self.resource_client.device_type1_volume_set_snapshots_list(
                self.resource_data["system_id"],
                self.resource_data['id'])
            response = api_response.to_dict()

            if response.get("items"):
                more_facts["snapshots"] = response["items"]

        return more_facts

def main():
    """
    """
    GreenLakeVolumeSetFactsModule().run()

if __name__ == '__main__':
    main()
