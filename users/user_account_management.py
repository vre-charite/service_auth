# Copyright 2022 Indoc Research
# 
# Licensed under the EUPL, Version 1.2 or – as soon they
# will be approved by the European Commission - subsequent
# versions of the EUPL (the "Licence");
# You may not use this work except in compliance with the
# Licence.
# You may obtain a copy of the Licence at:
# 
# https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12
# 
# Unless required by applicable law or agreed to in
# writing, software distributed under the Licence is
# distributed on an "AS IS" basis,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied.
# See the Licence for the specific language governing
# permissions and limitations under the Licence.
# 

# from flask import request
# from flask_restx import Resource

from fastapi import APIRouter
from fastapi_utils import cbv
from typing import Optional
from fastapi import Header
from config import ConfigSettings

from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
from models.user_account_management import UserADGroupOperationsPUT, \
    UserManagementV1PUT

from module_keycloak.ops_admin import OperationsAdmin

from services.data_providers.ldap_client import LdapClient
from services.data_providers.neo4j_client import Neo4jClient

from common.services.logger_services.logger_factory_service import SrvLoggerFactory

from resources.error_handler import catch_internal


router = APIRouter()

_API_TAG = 'v1/user/account'
_API_NAMESPACE = "api_user_management"
_logger = SrvLoggerFactory(_API_NAMESPACE).get_logger()


# the api is used to invite use into project
@cbv.cbv(router)
class UserADGroupOperations:

    def __init__(self):
        # self.__logger = SrvLoggerFactory('api_data_download').get_logger()
        pass

    @router.put("/user/ad-group", tags=[_API_TAG],
                 summary='add the target user to ad group')
    @catch_internal(_API_NAMESPACE)
    async def put(self, data: UserADGroupOperationsPUT):

        _logger.info('Call API for user ad group operations')

        res = APIResponse()
        try:

            operation_type = data.operation_type
            group_code = data.group_code
            user_email = data.user_email
           
            ldap_cli = LdapClient()
            # kc_cli = OperationsAdmin(realm)
            ldap_cli.connect(group_code)
            ldap_users_gotten = ldap_cli.get_user_by_email(user_email)
            user_dn = ldap_users_gotten[0]
            # user_entry = ldap_users_gotten[1]
            # operate on groups
            if operation_type == "remove":
                remove_result = ldap_cli.remove_user_from_group(user_dn)
            if operation_type == "add":
                add_result = ldap_cli.add_user_to_group(user_dn)
            ldap_cli.disconnect()

            res.result = {"message": "Succeed."}
            res.code = EAPIResponseCode.success
            
        except Exception as e:
            res.error_msg = {'error_message': "[Internal error]" + str(e)}
            res.code = EAPIResponseCode.internal_error

        return res.json_response()


# this api is used to dis/activate use
# this api will need to direct call the keycloak
@cbv.cbv(router)
class UserManagementV1:

    @router.put("/user/account", tags=[_API_TAG],
                 summary='add the new user to ad')
    @catch_internal(_API_NAMESPACE)
    async def put(self, data: UserManagementV1PUT,
        authorization: Optional[str] = Header(None)):
        
        _logger.info(
            'Call API for update user accounts')

        res = APIResponse()
        try:
            access_token = authorization
            # headers = {
            #     'Authorization': access_token
            # }
            if not access_token:
                res.error_msg = 'Access token required.'
                res.code = EAPIResponseCode.unauthorized
                return res.json_response()

            # req_body = request.get_json()
            operation_type = data.operation_type
            user_email = data.user_email
            user_geid = data.user_geid
            realm = data.realm
            operation_payload = data.payload
            # check parameters
            if not operation_type:
                res.error_msg = 'operation_type required.'
                res.code = EAPIResponseCode.bad_request
                return res.json_response()

            # check user identity
            if not user_email and not user_geid:
                res.error_msg = 'either user_email or user_geid required.'
                res.code = EAPIResponseCode.bad_request
                return res.json_response()

            # check user operation type
            if not operation_type in ['enable', 'restore', 'disable']:
                res.error_msg = 'operation {} is not allowed'.format(operation_type)
                res.code = EAPIResponseCode.bad_request
                return res.json_response()

            # status mapping
            user_status, user_relationship_status = {
                "enable": ("active", "hibernate"),
                "restore": ("active", "active"),
                "disable": ("disabled", "disable")
            }.get(operation_type)

            # init
            neo4j_client = Neo4jClient()
            kc_cli = OperationsAdmin(realm)

            # get user information
            respon_user_information = neo4j_client.get_user_by_geid(user_geid) if user_geid \
                else neo4j_client.get_user_by_email(user_email)
            if respon_user_information['code'] == 404:
                res.error_msg = 'User not found'
                res.code = EAPIResponseCode.bad_request
                return res.json_response()
            user_data = respon_user_information['result']
            user_current_status = user_data["status"]

            # validate operation type
            operation_validation = validate_operation_type(
                user_current_status, operation_type)
            if not operation_validation[0]:
                res.error_msg = "Invliad opertion type, User status: {}, Allowed operation types: {}"
                res.code = EAPIResponseCode.unauthorized
                return res.json_response()

            # Fetch all datasets that connected to the user
            respon_linked_projects = neo4j_client.get_user_linked_projects(
                user_data['id'])
            linked_projects = []
            if respon_linked_projects.status_code == 200:
                def decode_linked_projects(project_queried):
                    project_info = project_queried['end_node']
                    relation = project_queried['r']
                    decoded = {
                        "neo4j_id": project_info['id'],
                        "project_code": project_info['code'],
                        "relation_name": relation['type'],
                        'relation_status': relation['status'],
                        "ad_role": "{}-{}".format(project_info['code'], relation['type'])
                    }
                    return decoded

                linked_projects = [decode_linked_projects(
                    record) for record in respon_linked_projects.json()]

            # update keyclock, ldap project roles
            specified_project_code = operation_payload.get("project_code")
            if specified_project_code and operation_type == "restore":
                linked_projects = [project for project in linked_projects if specified_project_code ==
                                   project["project_code"]]
            try:
                for project in linked_projects:
                    if operation_type == "enable":
                        pass
                    elif operation_type == "restore":
                        if project["relation_status"] != "active":
                            on_project_restore(
                                user_data['email'], project, kc_cli, access_token)
                    elif operation_type == "disable":
                        if project["relation_status"] == "active":
                            on_project_disable(
                                user_data['email'], project, kc_cli, access_token)
            except Exception as e:
                res.error_msg = "relation update error: " + str(e)
                res.code = EAPIResponseCode.internal_error
                return res.json_response()
                
            # extra operations
            try:
                if operation_type == "disable":
                    remove_from_user_group(user_data['email'], kc_cli, access_token)
                if operation_type == "enable":
                    enable_from_user_group(user_data['email'], kc_cli, access_token)
            except Exception as e:
                return {"error_message": "remove/enable from users group error: " + str(e)}, 500

            # update user status in neo4j
            user_data['status'] = user_status
            neo4j_client.update_user(user_data['id'], user_data)

            # update neo4j relations
            for project in linked_projects:
                neo4j_client.update_relation(
                    user_data['id'], project['neo4j_id'], project['relation_name'], {'status': user_relationship_status}
                )

            res.result = {
                'user': user_data,
                'linked_projects': linked_projects,
            }
            res.code = EAPIResponseCode.success

        except Exception as e:
            _logger.error("[Internal error]" + str(e))
            res.error_msg = "[Internal error]" + str(e)
            res.code = EAPIResponseCode.internal_error

        return res.json_response()


def on_project_disable(email, project, kc_cli, access_token):
    ldap_user_grouppen = ConfigSettings.LDAP_USER_GROUP
    # ldap
    ldap_cli = LdapClient()
    ldap_cli.connect(project['project_code'])
    ldap_users_gotten = ldap_cli.get_user_by_email(email)
    user_dn = ldap_users_gotten[0]
    user_entry = ldap_users_gotten[1]
    _logger.info("removed project code: " + project['project_code'])
    _logger.info("removed user from group: " + user_dn)
    remove_result = ldap_cli.remove_user_from_group(user_dn)
    ldap_cli.disconnect()


def on_project_enable(email, project, kc_cli, access_token):
    pass


def on_project_restore(email, project, kc_cli, access_token):
    # update user in ad and keyclock
    user_keyclock = kc_cli.get_user_by_email(email)
    userid = user_keyclock['id']
    # keyclock
    keyclock_res = kc_cli.assign_user_role(userid, project["ad_role"])
    # ldap
    ldap_cli = LdapClient()
    ldap_cli.connect(project['project_code'])
    ldap_users_gotten = ldap_cli.get_user_by_email(email)
    user_dn = ldap_users_gotten[0]
    user_entry = ldap_users_gotten[1]
    result = ldap_cli.add_user_to_group(user_dn)
    ldap_cli.disconnect()


def remove_from_user_group(email, kc_cli, access_token):
    # ldap user grouppen
    ldap_cli = LdapClient()
    ldap_cli.connect(ConfigSettings.LDAP_USER_GROUP)
    ldap_users_gotten = ldap_cli.get_user_by_email(email)
    user_dn = ldap_users_gotten[0]
    user_entry = ldap_users_gotten[1]
    _logger.info("removed user dn: " + user_dn)
    remove_result = ldap_cli.remove_user_from_group(user_dn)
    ldap_cli.disconnect()


def enable_from_user_group(email, kc_cli, access_token):
    # ldap user grouppen
    ldap_cli = LdapClient()
    ldap_cli.connect(ConfigSettings.LDAP_USER_GROUP)
    ldap_users_gotten = ldap_cli.get_user_by_email(email)
    user_dn = ldap_users_gotten[0]
    user_entry = ldap_users_gotten[1]
    result = ldap_cli.add_user_to_group(user_dn)
    ldap_cli.disconnect()


def validate_operation_type(current_user_status, operation_type):
    '''
    validate operation type
    return tuple (True, allowed_operations)
    '''

    def allowed_opertions(status):
        return {
            "active": ["disable", "restore"],
            "disabled": ["enable"]
        }.get(status, [])

    allowed = allowed_opertions(current_user_status)
    return operation_type in allowed, allowed
