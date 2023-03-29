#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Hewlett Packard Enterprise Development LP.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = '''
---
module: greenlake_volume
short_description: Manage Greenlake Data Service volume resources.
description:
    - Provides an interface to manage Greenlake Data Service volume resources. Can create, update, and delete.
version_added: "2.13.8"
requirements:
    - python >= 3.8
    - greenlake_data_services >= 1.0.0
author: "Sijeesh Kattumunda (@sijeesh)"
options:
    state:
        description:
            - Indicates the desired state for the Greenlake Data Service volume resources.
              C(present) will ensure data properties are compliant with Greenlake Data Service.
              C(absent) will remove the resource from Greenlake Data Service, if it exists.
        choices: ['present', 'absent']
        required: true
        type: str
    data:
        description:
            - List with the Greenlake Data Service volume resource properties.
        required: true
        type: dict
'''

EXAMPLES = '''
- name: Create GreenLake DSCC Volume
  greenlake_volume:
    host: <host>
    client_id: <client_id>
    client_secret: <client_secret>
    system_id: "<system_id |default(omit>"
    state: present
    data:
      comments: "Ansible library test"
      count: 2
      data_reduction: True
      name: "AnsibleTestVolume"
      size_mib: 16384.0
      snap_cpg: "SSD_r6"
      user_cpg: "SSD_r6"

- debug: var=volumes

- name: Update GreenLake DSCC Volume
  greenlake_volume:
    host: <host>
    client_id: <client_id>
    client_secret: <client_secret>
    system_id: "<system_id |default(omit)>"
    state: present
    data:
      name: "AnsibleTestVolume"
      new_name: "AnsibleTestVolume_updated"
      size_mib: 16384.0
      snap_cpg: "SSD_r6"
      user_cpg: "SSD_r6"
- debug: var=volumes

- name: Delete GreenLake DSCC Volume
  greenlake_volume:
    host: <host>
    client_id: <client_id>
    client_secret: <client_secret>
    state: absent
    data:
      name: "AnsibleTestVolume"
'''

RETURN = '''
volumes:
    description: Has the facts about Greenlake Data Service volumes resources
    returned: On state 'present'. Can be null.
    type: dict
'''

from ansible_collections.hpe.greenlake_data_services.plugins.module_utils.greenlake import GreenLakeDataServiceModule, compare

from greenlake_data_services.api import volumes_api
from greenlake_data_services.model.volume_put import VolumePut
from greenlake_data_services.model.un_export_vlun import UnExportVlun


class VolumeModule(GreenLakeDataServiceModule):

    MSG_CREATED = "Volume resource created successfully"
    MSG_DELETED = "Volume resource deleted successfully"
    MSG_UPDATED = "Volume resource updated"
    MSG_ALREADY_PRESENT = 'Volume resource exists with the same details'

    UPDATE_FIELDS = ["conversion_type",
                     "name",
                     "size_mib",
                     "snapshot_alloc_warning",
                     "user_alloc_warning",
                     "user_cpg_name"]

    FIELDS_NAME_TO_REPLACE = {
        "size_mib": "size_mi_b"
    }

    FIELDS_DIFFENRENCE = {"snapshot_alloc_warning": "",
                          "user_alloc_warning": "",
                          "conversion_type": "",
                          "user_cpg_name":""}


    def __init__(self):

        additional_arg_spec = dict(data=dict(required=True, type='dict'),
                                   system_id=dict(type='str'),
                                   state=dict(
                                       required=True,
                                       choices=['present', 'absent']))

        super(VolumeModule, self).__init__(
            additional_arg_spec=additional_arg_spec)

        self.set_resource_client(volumes_api.VolumesApi(self.greenlake_client))
        self.set_resource_data()

    def get_resource_by_id_or_name(self, id=None, name=None):
        """
         Set resource data by passing id or name
        """
        return self.volume_get_by_id_or_name(id, name)

    def execute_module(self):
        changed, msg, ansible_facts = False, '', {}
        self.system_id = self.module.params.get('system_id')

        if self.state == 'present':
            return self._present()
        elif self.state == 'absent':
            changed, msg, ansible_facts = self._absent()

        return dict(changed=changed, msg=msg, ansible_facts=ansible_facts)

    def _present(self):
        ansible_facts, msg, changed = {"volumes": []}, "", False
        result = {}

        if self.resource_data:
            self.process_input_data(self.UPDATE_FIELDS)

            data_copy = self.data.copy()
            self.replace_field_names(data_copy, self.FIELDS_NAME_TO_REPLACE)

            merged_data = self.resource_data.copy()
            merged_data.update(data_copy)

            # Remove these fields as th fileds not there in get_by_id
            # id reseponse
            # conversion_type = self.data.pop("conversion_type", "")
            # user_cpg_name = self.data.pop("user_cpg_name", "")
            for field_name in self.FIELDS_DIFFENRENCE:
                self.FIELDS_DIFFENRENCE[field_name] = merged_data.pop(field_name, "")

            if (compare(self.resource_data, merged_data)
                    and not self.new_name):
                changed = False
                msg = self.MSG_ALREADY_PRESENT
            else:
                if self.new_name:
                    self.data[self.resource_name_field] = self.new_name

                # if conversion_type:
                #     self.data["conversion_type"] = conversion_type

                # if user_cpg_name:
                #     self.data["user_cpg_name"] = user_cpg_name
                # for field_name in self.FIELDS_DIFFENRENCE:
                #     self.data[field_name] = self.FIELDS_DIFFENRENCE[field_name]
                volume_put = VolumePut(**self.data)

                api_response = self.resource_client.volume_edit(
                    self.system_id,
                    self.resource_data["id"],
                    volume_put)

                result = self.get_task(api_response.to_dict())
                changed = True
                msg = self.MSG_UPDATED
        else:
            api_response = self.resource_client.volume_create(
                self.system_id, self.data)

            result = self.get_task(api_response.to_dict())
            msg = self.MSG_CREATED

        if result and not result.get("error"):
            self.set_resource_data()
            changed = True

        ansible_facts["volumes"].append(self.resource_data)

        return dict(
            msg=msg,
            changed=changed,
            ansible_facts=ansible_facts
        )

    def _delete_volume_snapshot(self, system_id, volume_id, snapshot_id):
        return self.delete_resource(
            ("/api/v1/storage-systems/device-type1/{system_id}/volumes/"
                "{volume_id}/snapshots/{snapshot}").format(
                    system_id=system_id,
                    volume_id=volume_id,
                    snapshot=snapshot_id))

    def _delete_volume_snapshots_all(self, system_id, id):
        api_response = self.resource_client.device_type1_volume_snapshots_list(
            system_id, id)
        response = api_response.to_dict()
        if response.get("items"):
            for snapshot in response.get("items"):
                self._delete_volume_snapshot(system_id, id, snapshot["id"])

    # (Device type1) Get host initiator groups
    def _device_type1_get_host_initiators(self):
        host_initiator_groups = self.resource_data['initiators']
        host_group_ids = []
        for host_inititaor_group in host_initiator_groups:
            host_group_ids.append(host_inititaor_group['id'])
        return host_group_ids

    def _volume_unexport(self, system_id, volume_id):
        host_group_ids = self._device_type1_get_host_initiators()
        un_export_vlun = UnExportVlun(host_group_ids=host_group_ids,)
        if un_export_vlun.get('host_group_ids') and len(un_export_vlun.get(
           'host_group_ids')) > 0:
            response = self.resource_client.device_type1_vlun_unexport(
                system_id, volume_id, un_export_vlun)
            return self.get_task(response.to_dict())

    def _absent(self):
        changed = False
        msg = self.MSG_DELETED
        un_export = True # bool | UnExport Host,HostSet and delete volume (optional)
        cascade = True # bool | Delete snapshot and volume (optional)

        if self.data.get("id") or self.data.get("name"):
            resource_id = self.resource_data["id"]
            api_response = self.resource_client.volume_get_by_id(resource_id)
            self.resource_data = api_response.to_dict()
            system_id = api_response.to_dict()["system_id"]
            self._delete_volume_snapshots_all(system_id, resource_id)
            self._volume_unexport(system_id, resource_id)

            api_response = self.resource_client.volume_delete(
                system_id, resource_id)

            changed = True

        return changed, msg, {}


def main():
    VolumeModule().run()


if __name__ == '__main__':
    main()
