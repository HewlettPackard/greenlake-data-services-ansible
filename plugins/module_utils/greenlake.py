#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Hewlett Packard Enterprise Development LP.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import abc
import collections
from glob import escape
import json
import logging
import os
import traceback
import time
import requests
from requests_oauthlib import OAuth2Session
from requests.auth import HTTPBasicAuth
from oauthlib.oauth2 import BackendApplicationClient

try:
    import greenlake_data_services
except ImportError:
    print("DSCC Python SDK is not installed")

try:
    from ansible.module_utils import six
    from ansible.module_utils._text import to_native
except ImportError:
    import six
    to_native = str

from ansible.module_utils.basic import AnsibleModule

from greenlake_data_services.api import tasks_api

logger = logging.getLogger(__name__)  # Logger for development purposes


def get_logger(mod_name):
    """
    To activate logs, setup the environment var LOGFILE
    Args:
        mod_name: module name
    Returns: Logger instance`
    """

    logger = logging.getLogger(os.path.basename(mod_name))
    global LOGFILE
    LOGFILE = os.environ.get('LOGFILE')

    if not LOGFILE:
        logger.addHandler(logging.NullHandler())
    else:
        logging.basicConfig(level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S',
                            format='%(asctime)s %(levelname)s %(name)s %(message)s',
                            filename=LOGFILE, filemode='a')
    return logger

class GreenLakeDataServiceModuleException(Exception):
    """
   GreenLake DataService ModuleException

    Attributes:
       msg (str): Exception message.
       green lake response (dict): Green Lake rest response.
   """

    def __init__(self, data):
        self.msg = None
        self.greenlake_response = None

        if isinstance(data, six.string_types):
            self.msg = data
        else:
            self.greenlake_response = data

            if data and isinstance(data, dict):
                self.msg = data.get('message')

        if self.greenlake_response:
            Exception.__init__(self, self.msg, self.greenlake_response)
        else:
            Exception.__init__(self, self.msg)


# @six.add_metaclass(abc.ABCMeta)
class GreenLakeDataServiceModule():
    MSG_CREATED = 'Resource created successfully.'
    MSG_UPDATED = 'Resource updated successfully.'
    MSG_DELETED = 'Resource deleted successfully.'
    MSG_ALREADY_PRESENT = 'Resource is already present.'
    MSG_ALREADY_ABSENT = 'Resource is already absent.'
    MSG_DIFF_AT_KEY = 'Difference found at key \'{0}\'. '
    MSG_MANDATORY_FIELD_MISSING = 'Missing mandatory field: name'
    PYTHON_SDK_REQUIRED = ('HPE GreenLake Data Service Python SDK'
                           'is required for this module.')

    GREENLAKE_ARGS = dict(
        config=dict(type='path'),
        host=dict(type='str'),
        client_id=dict(type='str', no_log=True),
        client_secret=dict(type='str')
    )

    def __init__(self, additional_arg_spec=None):
        """
        GreenLakeDataServiceModule constructor.

        :arg dict additional_arg_spec: Additional argument spec definition.
        """
        argument_spec = self._build_argument_spec(additional_arg_spec)

        self.module = AnsibleModule(argument_spec=argument_spec,
                                    supports_check_mode=False)

        self.resource_client = None
        self.resource_data = {}

        self.state = self.module.params.get('state')
        self.data = self.module.params.get('data', {})

        self.api_client_conf = {}
        self._create_greenlake_client()

        # Preload params for get_all - used by facts
        self.facts_params = self.module.params.get('params') or {}

        # Preload options as dict - used by facts
        self.options = transform_list_to_dict(
            self.module.params.get('options'))

        self.resource_id = self.module.params.get('id') or self.data.get('id')
        self.system_id = self.module.params.get('system_id')
        self.device_type = self.module.params.get('device_type')
        self.resource_name_field = "name"
        self.new_name = None

    def set_resource_data(self):
        """
        Set resource data
        """
        # To handle the name field inconsistency in resource data
        if self.resource_name_field != "name" and self.data.get("name"):
            self.data[self.resource_name_field] = self.data.pop("name")

        # Collect resource name.
        name = (self.module.params['name'] if self.module.params.get('name')
                else self.data.get(self.resource_name_field, ""))

        if name or self.resource_id:
            self.resource_data = self.get_resource_by_id_or_name(
                id=self.resource_id, name=name)

        new_name = self.data.pop("new_name", None)

        if ((name and new_name and name != new_name) or
                (self.resource_id and new_name and
                 new_name != self.resource_data[self.resource_name_field]
                 )):
            self.new_name = new_name
            # Assign new name value to the name field if the resource exists
            # if self.resource_data and self.new_name:
            #     self.data[self.resource_name_field] = self.new_name

    def process_input_data(self, fields):
        """
        Delete unsupported fieleds from the request input
        """
        for key in list(self.data):
            if key not in fields:
                del self.data[key]

    def replace_field_names(self, data, fields):
        """
        Delete unwanted fields from request input
        """
        for key in fields:
            if key in data:
                value = data.pop(key, "")
                data[fields[key]] = value

    def _build_argument_spec(self, additional_arg_spec):
        """
        Creates argument list by merging default arguments with additional
        arguments.
        """
        merged_arg_spec = dict()
        merged_arg_spec.update(self.GREENLAKE_ARGS)

        if additional_arg_spec:
            merged_arg_spec.update(additional_arg_spec)

        return merged_arg_spec

    def _get_config_from_json_file(self, file_name):
        """
        Construct Greenlake client using a json file.
        Args:
            file_name: json full path.
        Returns:
            Greenlake client object
        """
        with open(file_name) as json_data:
            config = json.load(json_data)

        return config

    def _get_access_token(self, client_id, client_secret):
        client = BackendApplicationClient(client_id)
        oauth = OAuth2Session(client=client)
        auth = HTTPBasicAuth(client_id, client_secret)
        token = oauth.fetch_token(
            token_url='https://sso.common.cloud.hpe.com/as/token.oauth2',
            auth=auth)

        return token["access_token"]

    def _create_greenlake_client(self):
        """
        Creates GreenLake client object using module prams/env variables/config
        file
        """
        if self.module.params.get('host'):
            host = self.module.params['host']
            client_id = self.module.params['client_id']
            client_secret = self.module.params['client_secret']
        elif self.module.params['config']:
            config = self._get_config_from_json_file(
                self.module.params['config'])
            host = config.get('host', '')
            client_id = config.get('client_id', '')
            client_secret = config.get('client_secret', '')
        else:
            host = os.environ.get('GREENLAKE_HOST', '')
            client_id = os.environ.get('GREENLAKE_CLIENT_ID', '')
            client_secret = os.environ.get('GREENLAKE_CLIENT_SECRET', '')

            if not host or not client_id or not client_secret:
                print("Make sure you have set mandatory env variables \
                (GREENLAKE_HOST, GREENLAKE_CLIENT_ID, \
                    GREENLAKE_CLIENT_SECRET)")

        access_token = self._get_access_token(client_id, client_secret)
        configuration = greenlake_data_services.Configuration(
            access_token=access_token,
            host=host
        )
        self.api_client_conf = {"access_token": access_token, "host": host}
        self.greenlake_client = greenlake_data_services.ApiClient(configuration)

    def set_resource_client(self, resource_client):
        """
        Sets the resource client
        """
        self.resource_client = resource_client

    def get_task_reponse(self, task):
        """Handle task reponse"""
        task_instance = tasks_api.TasksApi(self.greenlake_client)
        error = False
        while task.get("status") in ('INITIALIZED', 'RUNNING', 'SUBMITTED'):
            time.sleep(5)
            try:
                api_response = task_instance.get_task(task["task_uri"])
            except KeyError:
                api_response = task_instance.get_task(task["taskUri"])

            task = api_response.to_dict()
            if task.get("status") in ('FAILED', 'TIMEDOUT', 'PAUSED'):
                error = True
                break

            if task.get('state') == 'SUCCEEDED':
                break

        return task, error

    def get_task(self, task):
        error, response = False, {}
        response, error = self.get_task_reponse(task)

        if response.get("associated_resources"):
            task = response.get("associated_resources")
        elif response.get("child_tasks"):
            child_task = response.get("child_tasks")[0]
            task_uri = child_task["resource_uri"]
            task_req = {"status": "INITIALIZED",
                        "taskUri": task_uri.split('/')[-1],
                        'message': ''}
            task, error = self.get_task_reponse(task_req)

        if(task.get("response") and
           task["response"].get("state") == "SUCCEEDED"):
            error = False

        return {"error": error,
                "message": task.get("message", ""),
                "response": task}

    @abc.abstractmethod
    def set_resource_by_id_or_name(self):
        """
        Abstract method must be implemented by the inheritor.
        """

    @abc.abstractmethod
    def execute_module(self):
        """
        Abstract method, must be implemented by the inheritor.

        This method is called from the run method. It should contain
        the module logic

        :return: dict: It must return a dictionary with the attributes
        for the module result,
            such as ansible_facts, msg and changed.
        """
        pass

    def run(self):
        """
        Common implementation of the Greenlake Data Service run modules.

        It calls the inheritor 'execute_module' function and sends
        the return to the Ansible.

        It handles any GreenLakeDataServiceModuleException in order to
        signal a failure to Ansible, with a descriptive error message.

        """
        try:
            result = self.execute_module()

            if not result:
                result = {}

            if "changed" not in result:
                result['changed'] = False

            self.module.exit_json(**result)

        except GreenLakeDataServiceModuleException as exception:
            error_msg = '; '.join(to_native(e) for e in exception.args)
            self.module.fail_json(msg=error_msg,
                                  exception=traceback.format_exc())

    def get_api_header(self):
        return {
            'Authorization': 'Bearer ' + self.api_client_conf["access_token"],
            'Content-type': 'application/json'}

    def get_resource_url(self, path):
        host_url = self.api_client_conf["host"]
        url = host_url + path
        return url

    def get_resource(self, path, params={}):
        response = requests.get(
            self.get_resource_url(path),  headers=self.get_api_header(),
            params=params,)
        return self.get_task(response.json())

    def delete_resource(self, path):
        response = requests.delete(self.get_resource_url(path),
                                   headers=self.get_api_header())
        return self.get_task(response.json())

    def post_resource(self, path, data):
        response = requests.post(self.get_resource_url(path),
                                 headers=self.get_api_header(),  data=data)
        return self.get_task(response.json())

    def host_group_get_by_id_or_name(self, id, name):
        """
        Method to help getting the host group resource data by name or id
        """
        resource = {}

        if id:
            response = self.resource_client.host_group_get_by_id(id)
            resource =  eval(response.to_str())
        elif name:
            name = escape(name)
            filter = "name eq '"+name+"'"
            response = self.resource_client.host_group_list(filter=filter)

            if response.to_dict().get("items"):
                resource = eval(response.to_str()).get("items",[])[0]

        return resource

    def host_get_by_id_or_name(self, id, name):
        """
        Method to help getting the host resource data by name or id
        """
        resource = {}

        if id:
            response = self.resource_client.host_get_by_id(id)
            resource = eval(response.to_str())
        elif name:
            name = escape(name)
            filter = "name eq '"+name+"'"
            response = self.resource_client.host_list(filter=filter)

            if response.to_dict().get("items"):
                resource = eval(response.to_str()).get("items",[])[0]

        return resource

    def host_initiator_get_by_id_or_name(self, id, name):
        """
        Method to help getting the host initiator resource data by name or id
        """
        resource = {}

        if id:
            response = self.resource_client.host_initiator_get_by_id(id)
            resource = eval(response.to_str())
        elif name:
            name = escape(name)
            filter = "name eq '"+name+"'"
            response = self.resource_client.host_initiator_list(filter=filter)

            if response.to_dict().get("items"):
                resource = eval(response.to_str()).get("items",[])[0]

        return resource

    def volume_get_by_id_or_name(self, id, name):
        """
        Method to help getting the volume resource data by name or id
        """
        resource = {}
        if id:
            response = self.resource_client.volume_get_by_id(id)
            resource = eval(response.to_str())
        elif name:
            name = escape(name)
            filter = "name eq '"+name+"'"
            response = self.resource_client.volumes_list(filter=filter)

            if response.to_dict().get("items"):
                resource = eval(response.to_str()).get("items",[])[0]

        return resource

    def volume_set_get_by_id_or_name(self, system_id, id=None, name=None):
        """
        Method to help getting the volumeset resource data by name or id
        """
        resource = {}

        if self.device_type == "1":
            if id:
                response = self.resource_client.device_type1_volume_sets_get_by_id(
                    id, system_id)
                resource = eval(response.to_str())
            else:
                name = escape(name)
                filter = "name eq '"+name+"'"

                response = self.resource_client.device_type1_volume_sets_list(
                    system_id, filter=filter)

                if response.to_dict().get("items"):
                    resource = eval(response.to_str()).get("items",[])[0]
        else:
            pass  # TODO need to implement for device type 2

        return resource

def transform_list_to_dict(list_):
    """
    Transforms a list into a dictionary, putting values as keys.

    :arg list list_: List of values
    :return: dict: dictionary built
    """

    ret = {}

    if not list_:
        return ret

    for value in list_:
        if isinstance(value, collections.Mapping):
            ret.update(value)
        else:
            ret[to_native(value)] = True

    return ret

def _str_sorted(obj):
    if isinstance(obj, collections.Mapping):
        return json.dumps(obj, sort_keys=True)
    else:
        return str(obj)

def _standardize_value(value):
    """
    Convert value to string to enhance the comparison.

    :arg value: Any object type.

    :return: str: Converted value.
    """
    if isinstance(value, float) and value.is_integer():
        # Workaround to avoid erroneous comparison between int and float
        # Removes zero from integer floats
        value = int(value)

    return str(value)

def compare(first_resource, second_resource):
    """
    Recursively compares dictionary contents equivalence,
    ignoring types and elements order.
    Particularities of the comparison:
        - Inexistent key = None
        - These values are considered equal: None, empty, False
        - Lists are compared value by value after
          a sort, if they have same size.
        - Each element is converted to str before the comparison.
    :arg dict first_resource: first dictionary
    :arg dict second_resource: second dictionary
    :return: bool: True when equal, False when different.
    """
    resource1 = first_resource
    resource2 = second_resource

    debug_resources = "resource1 = {0}, resource2 = {1}".format(
        resource1, resource2)

    # The first resource is True / Not Null and the second
    # resource is False / Null
    if resource1 and not resource2:
        logger.debug("resource1 and not resource2. " + debug_resources)
        return False

    # Checks all keys in first dict against the second dict
    for key in resource1:
        if key not in resource2:
            if resource1[key] is not None:
                # Inexistent key is equivalent to exist with value None
                # + debug_resources)
                return False
        # If both values are null, empty or False it will be considered equal.
        elif not resource1[key] and not resource2[key]:
            continue
        elif isinstance(resource1[key], collections.Mapping):
            # recursive call
            if not compare(resource1[key], resource2[key]):
                # + debug_resources)
                return False
        elif isinstance(resource1[key], list):
            # change comparison function to compare_list
            if not compare_list(resource1[key], resource2[key]):
                # + debug_resources)
                return False
        elif (_standardize_value(resource1[key])
              != _standardize_value(resource2[key])):
            # + debug_resources)
            return False

    # Checks all keys in the second dict, looking for missing elements
    for key in resource2.keys():
        if key not in resource1:
            if resource2[key] is not None:
                # Inexistent key is equivalent to exist with value None
                # + debug_resources)
                return False
    return True

def compare_list(first_resource, second_resource):
    """
    Recursively compares lists contents equivalence, ignoring types
    and element orders.
    Lists with same size are compared value by value after a sort,
    each element is converted to str before the comparison.
    :arg list first_resource: first list
    :arg list second_resource: second list
    :return: True when equal; False when different.
    """

    resource1 = first_resource
    resource2 = second_resource

    debug_resources = "resource1 = {0}, resource2 = {1}".format(
        resource1, resource2)

    # The second list is null / empty  / False
    if not resource2:
        logger.debug("resource 2 is null. " + debug_resources)
        return False

    if len(resource1) != len(resource2):
        logger.debug("resources have different length. " + debug_resources)
        return False

    resource1 = sorted(resource1, key=_str_sorted)
    resource2 = sorted(resource2, key=_str_sorted)

    for i, val in enumerate(resource1):
        if isinstance(val, collections.Mapping):
            # change comparison function to compare dictionaries
            if not compare(val, resource2[i]):
                logger.debug("resources are different. " + debug_resources)
                return False
        elif isinstance(val, list):
            # recursive call
            if not compare_list(val, resource2[i]):
                logger.debug("lists are different. " + debug_resources)
                return False
        elif _standardize_value(val) != _standardize_value(resource2[i]):
            logger.debug("values are different. " + debug_resources)
            return False

    # no differences found
    return True
