#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Hewlett Packard Enterprise Development LP.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = '''
---
module: greenlake_host_initiator_facts
short_description: Retrieve the facts about host initiators
description:
    - Retrieve the facts about one or more of the HPE Greenlake Data Services host initiators
version_added: "2.13.8"
requirements:
    - python >= 3.8
    - greenlake_data_services >= 1.0.0
author: "Sijeesh Kattumunda (@sijeesh)"
options:
    id:
      description:
        - Id of the Greenlake Data Service host initiators.
      required: false
      type: str
    params:
      description:
        - List of params to delimit, filter and sort the list of resources.
        - "params allowed:
            C(filter): "id eq 2a0df0fe6f7dc7bb16000000000000000000004817" # str | oData query to filter hostservice by Key. (optional)
            C(sort): str | oData query to sort hostservice by Key. (optional)
            C(limit): int | Number of items to return at a time (optional)
            C(offset): int | The offset of the first item in the collection to return (optional)"
      required: false
      type: dict
'''

EXAMPLES = '''
- name: Get GreenLake Data Service host resources
  greenlake_host_initiator_facts:
    host: <host>
    client_id: <client_id>
    client_secret: <client_secret>
- debug: var=host_initiators
'''

RETURN = '''
host_initiators:
    description: Has all the Greenlake Data Service facts about the host initiators resources.
    returned: Always, but can be null.
    type: dict
'''

from ansible_collections.hpe.greenlake_data_services.plugins.module_utils.greenlake import GreenLakeDataServiceModule
from greenlake_data_services.api import host_initiators_api


class GreenLakeHostInitiatorFactsModule(GreenLakeDataServiceModule):

    def __init__(self):
        argument_spec = dict(id=dict(type='str'),
                             params=dict(type='dict'))

        super(GreenLakeHostInitiatorFactsModule, self).__init__(
            additional_arg_spec=argument_spec)

        self.set_resource_client(host_initiators_api.HostInitiatorsApi(
            self.greenlake_client))

        self.set_resource_data()

    def get_resource_by_id_or_name(self, id=None, name=None):
        """
         Set resource data by passing id or name
        """
        return self.host_initiator_get_by_id_or_name(id, name)

    def execute_module(self):
        ansible_facts = {'host_initiators': []}

        if self.module.params.get('id'):
            ansible_facts["host_initiators"].append(self.resource_data)
        else:
            api_response = self.resource_client.host_initiator_list(
                **self.facts_params)
            ansible_facts["host_initiators"] = (
                ansible_facts["host_initiators"] +
                eval(api_response.to_str()).get("items", []))

        return dict(changed=False, ansible_facts=ansible_facts)


def main():
    GreenLakeHostInitiatorFactsModule().run()


if __name__ == '__main__':
    main()
