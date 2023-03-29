#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Hewlett Packard Enterprise Development LP.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = '''
---
module: greenlake_volume_facts
short_description: Retrieve the facts about volumes
description:
    - Retrieve the facts about one or more of the HPE Greenlake Data Services volume resources
version_added: "2.13.8"
requirements:
    - python >= 3.8
    - greenlake_data_services >= 1.0.0
author: "Sijeesh Kattumunda (@sijeesh)"
options:
    id:
      description:
        - Id of the Greenlake Data Service volume resource.
      required: false
      type: str
    name:
      description:
        - Name of the Greenlake Data Service volume resource.
      required: false
      type: str
    options:
      description:
        - "List with options to gather additional facts about Greenlake Data Service volume resources.
          Options allowed:
          getSnapshots get lsit of snapshots
        - "To gather facts about getSnapshots
           a Volume name/id is required. Otherwise, these options will be ignored."
      type: list
    params:
      description:
        - List of params to delimit, filter and sort the list of resources.
        - "params allowed:
           C(limit): int | Number of items to return at a time (optional)
           C(offset): int | The offset of the first item in the collection to return (optional)
           C(filter): "name eq array1 and wwn eq 2FF70002AC018D94" # str | oData query to filter by Key. (optional)
           C(sort): "systemWWN desc" # str | oData query to sort by Key. (optional)
           C(select): "id" # str | Query to select only the required parameters, separated by . if nested (optional)
      required: false
      type: dict
'''
EXAMPLES = '''
- name: Get GreenLake Data Service volume resources
  greenlake_volume_facts:
    host: <host>
    client_id: <client_id>
    client_secret: <client_secret>
- debug: var=volumes
'''

RETURN = '''
volumes:
    description: Has all the Greenlake Data Service facts about the volume resources.
    returned: Always, but can be null.
    type: dict
'''

from ansible_collections.hpe.greenlake_data_services.plugins.module_utils.greenlake import GreenLakeDataServiceModule, compare
from greenlake_data_services.api import volumes_api


class GreenLakeVolumeFactsModule(GreenLakeDataServiceModule):

    def __init__(self):
        argument_spec = dict(id=dict(type='str'),
                             name=dict(type='str'),
                             options=dict(type='list'),
                             params=dict(type='dict'))

        super(GreenLakeVolumeFactsModule, self).__init__(
            additional_arg_spec=argument_spec)

        self.set_resource_client(volumes_api.VolumesApi(self.greenlake_client))
        self.set_resource_data()

    def get_resource_by_id_or_name(self, id=None, name=None):
        """
         Set resource data by passing id or name
        """
        return self.volume_get_by_id_or_name(id, name)

    def execute_module(self):
        ansible_facts = {'volumes': []}

        if self.module.params.get('id') or self.module.params.get('name'):
            ansible_facts["volumes"].append(self.resource_data)
            if self.options:
                more_facts = self.__gather_optional_facts(ansible_facts)
                ansible_facts.update(more_facts)
        else:
            api_response = self.resource_client.volumes_list(
                **self.facts_params)

            ansible_facts["volumes"] = api_response.to_dict()["items"]

        return dict(changed=False, ansible_facts=ansible_facts)

    def __gather_optional_facts(self, ansible_facts):
        more_facts = {"snapshots": []}

        if self.options.get('getSnapshots'):
            response = self.resource_client.device_type1_volume_snapshots_list(
                ansible_facts["volumes"][0]["system_id"],
                self.module.params['id'])

            resource = response.to_dict()
            if resource.get("items"):
                more_facts["snapshots"] = resource["items"]

        return more_facts


def main():
    GreenLakeVolumeFactsModule().run()


if __name__ == '__main__':
    main()
