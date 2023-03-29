#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Hewlett Packard Enterprise Development LP.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = '''
---
module: greenlake_volume_facts
short_description: Manage Greenlake Data Service volumeset resources.
description:
    - Provides an interface to manage Greenlake Data Service volumeset resources. Can create, update, and delete.
version_added: "2.4.0"
requirements:
    - python >= 3.8
    - greenlake_data_services >= 1.0.0
author: "Sijeesh Kattumunda (@sijeesh)"
options:
    state:
        description:
            - Indicates the desired state for the Greenlake Data Service volumeset resources.
              C(present) will ensure data properties are compliant with Greenlake Data Service.
              C(absent) will remove the resource from Greenlake Data Service, if it exists.
        choices: ['present', 'absent']
        required: true
        type: str
    data:
        description:
            - List with the Greenlake Data Service volumeset resource properties.
        required: true
        type: dict
'''

EXAMPLES = '''
- name: Create GreenLake DSCC Volume Set
  greenlake_volumeset:
    host: <host>
    client_id: <client_id>
    client_secret: <client_secret>
    device_type: 1
    system_id: <system_id>"
    state: present
    data:
      # app_set_business_unit: "HPE"
      # app_set_comments: "Edit"
      app_set_importance: "MEDIUM"
      app_set_name: "ansble-test-volumeset"
      name: "ansible_volume_set"
      app_set_type: "OTHER"

- debug: var=volume_sets

- name: Update name of the DSCC Volume Set
  greenlake_volumeset:
    host: <host>
    client_id: <client_id>
    client_secret: <client_secret>
    device_type: 1
    system_id: <system_id>"
    state: present
    data:
      name: "ansble-test-volumeset"
      new_name: "ansble-test-volumeset_updated"
- debug: var=volume_sets

- name: Update GreenLake DSCC Volume Set with volumes
  greenlake_volumeset:
    host: <host>
    client_id: <client_id>
    client_secret: <client_secret>
    device_type: 1
     system_id: <system_id>"
    state: present
    data:
      name: "ansble-test-volumeset_updated"
      app_set_type: "OTHER"
      members:
        - "AnsibleTestVolume.0"
        - "AnsibleTestVolume.1"

- debug: var=volume_sets

- name: Export GreenLake DSCC Volume Set from system
  greenlake_volumeset:
    host: <host>
    client_id: <client_id>
    client_secret: <client_secret>
    device_type: 1
    system_id: <system_id>"
    state: export
    data:
      name: "ansble-test-volumeset"
      host_group_ids:
        - "7711267b21c145b9b65f84dbd0122acd"

- debug: var=volume_sets

- name: Delete GreenLake DSCC Volume Set
  greenlake_volumeset:
    host: <host>
    client_id: <client_id>
    client_secret: <client_secret>
    device_type: 1
    system_id: <system_id>"
    state: absent
    data:
      name: "ansble-test-volumeset"

- debug: var=volume_sets
'''

RETURN = '''
volume_sets:
    description: Has the facts about Greenlake Data Service volumesets resources
    returned: On state 'present'. Can be null.
    type: dict
'''

from ansible_collections.hpe.greenlake_data_services.plugins.module_utils.greenlake import GreenLakeDataServiceModule, compare
from greenlake_data_services.api import volume_sets_api
from greenlake_data_services.model.create_app_set_input import CreateAppSetInput
from greenlake_data_services.model.volume_set_put import VolumeSetPut
from greenlake_data_services.model.export_app_set_post import ExportAppSetPost
from greenlake_data_services.model.un_export_app_set_post import UnExportAppSetPost


class VolumeSetModule(GreenLakeDataServiceModule):

    MSG_DELETED = "Volume Set deleted successfully"
    MSG_UPDATED = "Volume Set resource updated"
    MSG_ALREADY_PRESENT = 'Volume Set resource exists with the same details'

    FEILDS_TO_REPLACE_FOR_UPDATE = ["app_set_type"]

    def __init__(self):

        additional_arg_spec = dict(data=dict(required=True, type='dict'),
                                   system_id=dict(type='str'),
                                   state=dict(
                                       required=True,
                                       choices=['present', 'absent', 'export'],
                                       ),
                                   device_type=dict(
                                       required=True,
                                       choices=['1', '2'],
                                       ),
                                   )

        super(VolumeSetModule, self).__init__(
            additional_arg_spec=additional_arg_spec)

        self.set_resource_client(volume_sets_api.VolumeSetsApi
                                 (self.greenlake_client))

        self.resource_name_field = "app_set_name"
        self.set_resource_data()

    def get_resource_by_id_or_name(self, id=None, name=None):
        """
         Set resource data by passing id or name
        """
        resource = self.volume_set_get_by_id_or_name(self.system_id, id, name)
        return resource

    def execute_module(self):
        changed, msg, ansible_facts = False, '', {}

        if self.state == 'present':
            changed, msg, ansible_facts = self._present()
        elif self.state == 'absent':
            changed, msg, ansible_facts = self._absent()
        elif self.state == 'export':
            changed, msg, ansible_facts = self._export()
        elif self.state == 'unexport':
            changed, msg, ansible_facts = self._unexport()

        return dict(changed=changed, msg=msg, ansible_facts=ansible_facts)

    def _update_resource(self, system_id, resource_id, volume_set_put):
        """
        Helper method to update volume set resource
        """
        api_response = self.resource_client.device_type1_volume_sets_edit_by_id(
            system_id, resource_id, volume_set_put)

        return self.get_task(api_response.to_dict())

    def _present(self):
        ansible_facts, msg, changed = {"volume_sets": []}, "", False
        result = {}

        if self.resource_data:
            # Remove this from data for comparison as the field names
            # are different
            add_members = self.data.pop("add_members", [])
            remove_members = self.data.pop("remove_members", [])

            members_to_be_removed = [
                member for member in remove_members
                if member in self.resource_data["members"]]

            members_to_be_added = [
                member for member in add_members
                if member not in self.resource_data["members"]]

            if add_members:
                # To make the comparion easy, assign add_members
                # field to members field(field that holds the list of members
                # in the resource data)
                self.data["members"] = add_members

            # To handle mismatch of fields value(case) in request and response
            for i in self.FEILDS_TO_REPLACE_FOR_UPDATE:
                if self.data.get(i):
                    self.resource_data[i]=self.data[i]

            merged_data = self.resource_data.copy()
            merged_data.update(self.data)

            if (compare(self.resource_data, merged_data)
                    and not members_to_be_added and not members_to_be_removed
                    and not self.new_name):
                changed = False
                msg = self.MSG_ALREADY_PRESENT
            else:
                self.data.pop("members", None)
                if members_to_be_added:
                    self.data["add_members"] = members_to_be_added

                if members_to_be_removed:
                    self.data["remove_members"] = members_to_be_removed

                if self.new_name:
                    self.data[self.resource_name_field] = self.new_name

                volume_set_put = VolumeSetPut(**self.data)

                result = self._update_resource(
                    self.system_id, self.resource_data['id'], volume_set_put)
                changed = True
                msg = self.MSG_UPDATED
        else:
            create_app_set_input = CreateAppSetInput(**self.data)

            api_response = self.resource_client.device_type1_volume_sets_create(
                self.system_id, create_app_set_input)

            result = self.get_task(api_response.to_dict())

        if result and not result.get("error"):
            self.set_resource_data()
            changed = True

        # Set facts
        ansible_facts["volume_sets"].append(self.resource_data)

        return changed, msg, ansible_facts

    def _absent(self):
        changed = False
        msg = self.MSG_DELETED

        if self.data.get("id") or self.data.get(self.resource_name_field):
            system_id = self.resource_data["system_id"]
            id = self.resource_data["id"]
            self._delete_volumeset_snapshots_all(system_id, id)

            api_response = self.resource_client.device_type1_volume_sets_delete_by_id(
                system_id,  id)
            self.get_task(api_response.to_dict())
            changed = True
        else:
            msg = "Resource already deleted"

        return changed, msg, {}

    def _export(self):
        ansible_facts, msg, changed = {"volume_sets": []}, "", False
        if self.data.get("id") or  self.data.get(self.resource_name_field):

            resource_id = self.resource_data["id"]
            export_app_set_post = ExportAppSetPost(
                host_group_ids=self.data.get("host_group_ids", []))

            # Export applicationset identified by {appsetId} from Primera
            # / Alletra 9K identified by {systemId}
            api_response = self.resource_client.device_type1_volume_set_export(
                 self.system_id, resource_id, export_app_set_post)

            result = self.get_task(api_response.to_dict())

            if result and not result.get("error"):
                self.set_resource_data()
                changed = True

            ansible_facts["volume_sets"].append(self.resource_data)

        return changed, msg, ansible_facts

    def _unexport(self):
        ansible_facts, msg, changed = {"volume_sets": []}, "", False
        if self.data.get("id") or self.data.get("name"):
            un_export_app_set_post = UnExportAppSetPost(
                host_group_ids=self.data.get("host_group_ids", []))

            # Unexport applicationset identified by {appsetId} from Primera /
            # Alletra 9K identified by {systemId}
            response = self.resource_client.device_type1_volume_set_unexport(
                self.system_id,
                self.resource_data["id"],
                un_export_app_set_post)

            result = self.get_task(response.to_dict())

            if result and not result.get("error"):
                self.set_resource_data()
                changed = True

        ansible_facts["volume_sets"].append(self.resource_data)

        return changed, msg, ansible_facts

    def _delete_volumeset_snapshot(self,
                                   system_id, volume_set_id, snapshot_id):
        return self.delete_resource(
            "/api/v1/storage-systems/device-type1/{system_id}/applicationsets/{volume_set_id}/snapshots/{snapshot_id}".format(
                system_id=system_id,
                volume_set_id=volume_set_id,
                snapshot_id=snapshot_id))

    def _delete_volumeset_snapshots_all(self, system_id, volume_set_id):
        api_response = self.resource_client.device_type1_volume_set_snapshots_list(system_id, volume_set_id)
        response = api_response.to_dict()

        if response.get("items"):
            for snapshot in response.get("items"):
                self._delete_volume_snapshot(
                    system_id, volume_set_id, snapshot["id"])


def main():
    '''
    Main method
    '''
    VolumeSetModule().run()


if __name__ == '__main__':
    main()
