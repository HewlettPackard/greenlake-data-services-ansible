#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Hewlett Packard Enterprise Development LP.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = '''
---
module: greenlake_audit_events_facts
short_description: Retrieve the facts about Audit Logs
description:
    - Retrieve the facts about one or more of the HPE Greenlake Data Services Audit Logs
version_added: "2.13.8"
requirements:
    - python >= 3.8
    - greenlake_data_services >= 1.0.0
author: "Sijeesh Kattumunda (@sijeesh)"
options:
    params:
      description:
        - List of params to delimit, filter and sort the list of resources.
        - "params allowed:
           C(filter): Filter criteria - e.g. state eq Failure and occurredAt gt 2020-09-08T16:51:33Z (optional)
           C(limit): The number of results to return (optional)
           C(offset): The number of results to skip (optional)
           C(sort): The sort order of the returned data set.
           C(select): A list of properties to include in the response. Currently only support returning of all fields. (optional)"
      required: false
      type: dict
'''

EXAMPLES = '''
- name: Get GreenLake Audit Events
  greenlake_audit_events_facts:
    host: <host>
    client_id: <client_id>
    client_secret: <client_secret>
- debug: var=events
'''

RETURN = '''
events:
    description: Has all the Greenlake Data Service facts about the audit logs.
    returned: Always, but can be null.
    type: dict
'''

from ansible_collections.hpe.greenlake_data_services.plugins.module_utils.greenlake import GreenLakeDataServiceModule
from greenlake_data_services.api import audit_api


class GreenLakeEventsFactsModule(GreenLakeDataServiceModule):

    def __init__(self):
        argument_spec = dict(params=dict(type='dict'))

        super(GreenLakeEventsFactsModule, self).__init__(
            additional_arg_spec=argument_spec)

        self.set_resource_client(audit_api.AuditApi(self.greenlake_client))

    def execute_module(self):
        facts = {'events': []}
        api_response = self.resource_client.audit_events_get(
            **self.facts_params)
        facts["events"] = facts["events"] + api_response.to_dict()["items"]
        return dict(changed=False, ansible_facts=facts)


def main():
    GreenLakeEventsFactsModule().run()


if __name__ == '__main__':
    main()
