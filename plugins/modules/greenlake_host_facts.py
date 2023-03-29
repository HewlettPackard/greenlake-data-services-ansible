#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Hewlett Packard Enterprise Development LP.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = '''
---
module: greenlake_host_facts
short_description: Retrieve the facts about hosts
description:
    - Retrieve the facts about one or more of the HPE Greenlake Data Services host resources
version_added: "2.13.8"
requirements:
    - python >= 3.8
    - greenlake_data_services >= 1.0.0
author: "Sijeesh Kattumunda (@sijeesh)"
options:
    id:
      description:
        - Id of the Greenlake Data Service host resource.
      required: false
      type: str
    name:
      description:
        - Name of the Greenlake Data Service host resource.
      required: false
      type: str
    options:
      description:
        - "List with options to gather additional facts about Greenlake Data Service host resources.
          Options allowed:
          C(getVolumes) get lsit of volumes
        - "To gather facts about getVolumes
           a Host name/id is required. Otherwise, these options will be ignored."
      type: list
    params:
      description:
        - List of params to delimit, filter and sort the list of resources.
        - "params allowed:
           C(filter): "id eq 2a0df0fe6f7dc7bb16000000000000000000004817" # str | oData query to filter hostservice by Key. (optional)
           C(limit): int | Number of items to return at a time (optional)
           C(offset): int | The offset of the first item in the collection to return (optional)
           C(sort): str | oData query to sort hostservice by Key. (optional)"
      required: false
      type: dict
'''

EXAMPLES = '''
- name: Get GreenLake Data Service host resources
  greenlake_host_facts:
    host: <host>
    client_id: <client_id>
    client_secret: <client_secret>
- debug: var=hosts
'''

RETURN = '''
hosts:
    description: Has all the Greenlake Data Service facts about the host resources.
    returned: Always, but can be null.
    type: dict
'''

from ansible_collections.hpe.greenlake_data_services.plugins.module_utils.greenlake import GreenLakeDataServiceModule
from greenlake_data_services.api import host_initiators_api


class GreenLakeHostFactsModule(GreenLakeDataServiceModule):

    def __init__(self):
        argument_spec = dict(id=dict(type='str'),
                             name=dict(type='str'),
                             options=dict(type='list'),
                             params=dict(type='dict'))

        super(GreenLakeHostFactsModule, self).__init__(
            additional_arg_spec=argument_spec)

        self.set_resource_client(
            host_initiators_api.HostInitiatorsApi(self.greenlake_client))

        self.set_resource_data()

    def get_resource_by_id_or_name(self, id=None, name=None):
        """
         Set resource data by passing id or name
        """
        return self.host_get_by_id_or_name(id, name)

    def execute_module(self):
        ansible_facts = {'hosts': []}
        if self.module.params.get('id') or self.module.params.get('name'):
            ansible_facts["hosts"].append(self.resource_data)
            if self.options:
                more_facts = self.__gather_optional_facts()
                ansible_facts.update(more_facts)
        else:
            api_response = self.resource_client.host_list(**self.facts_params)
            ansible_facts["hosts"] = eval(str(api_response["items"]))

        return dict(changed=False, ansible_facts=ansible_facts)

    def __gather_optional_facts(self):
        more_facts = {}

        if self.options.get('getVolumes'):
            api_response = self.resource_client.volumeset_get_byvolumeset_id(
                self.module.params['id'])
            response = api_response.to_dict()
            if response.get("items"):
                more_facts["volumes"] = response["items"]

        return more_facts


def main():
    GreenLakeHostFactsModule().run()


if __name__ == '__main__':
    main()
