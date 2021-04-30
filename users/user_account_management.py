import json
import requests
from flask import request
from flask_restx import Resource, fields
from services.data_providers.neo4j_client import Neo4jClient
from services.data_providers.ldap_client import LdapClient
from module_keycloak.ops_admin import OperationsAdmin
from config import ConfigClass
from models.api_response import APIResponse, EAPIResponseCode
from services.logger_services.logger_factory_service import SrvLoggerFactory

_logger = SrvLoggerFactory('user_management').get_logger()


class UserADGroupOperations(Resource):
    def put(self):
        '''
        API for user ad group operations
        '''
        _logger.info(
            'Call API for user ad group operations')
        try:
            access_token = request.headers.get('Authorization', None)
            if not access_token:
                return {'result': 'Access token required.'}, 403
            headers = {
                'Authorization': access_token
            }
            req_body = request.get_json()
            operation_type = req_body.get('operation_type', None)
            group_code = req_body.get('group_code', None)
            user_email = req_body.get('user_email', None)
            realm = req_body.get('realm', 'vre')
            if not group_code:
                return {"error_message": "group_code required"}, 403
            if not operation_type:
                return {"error_message": "operation_type required"}, 403
            if not user_email:
                return {"error_message": "user_email required"}, 403
            expected_operations = ["remove", "add"]
            ldap_cli = LdapClient()
            kc_cli = OperationsAdmin(realm)
            ldap_cli.connect(group_code)
            ldap_users_gotten = ldap_cli.get_user_by_email(user_email)
            user_dn = ldap_users_gotten[0]
            user_entry = ldap_users_gotten[1]
            # operate on groups
            if operation_type == "remove":
                remove_result = ldap_cli.remove_user_from_group(user_dn)
            if operation_type == "add":
                add_result = ldap_cli.add_user_to_group(user_dn)
            ldap_cli.disconnect()
            # keyclock synchronize
            kc_cli.sync_user_trigger()
            return {"message": "Succeed."}, 200
        except Exception as e:
            return {'error_message': "[Internal error]" + str(e)}, 500


class UserManagementV1(Resource):
    def put(self):
        _logger.info(
            'Call API for update user accounts')
        try:
            access_token = request.headers.get('Authorization', None)
            headers = {
                'Authorization': access_token
            }
            if not access_token:
                return {'result': 'Access token required.'}, 403
            req_body = request.get_json()
            operation_type = req_body.get('operation_type', None)
            user_email = req_body.get('user_email', None)
            user_geid = req_body.get('user_geid', None)
            realm = req_body.get('realm', 'vre')
            operation_payload = req_body.get('payload', {})
            # check parameters
            if not operation_type:
                return {'result': 'operation_type required.'}, 400
            # check user identity
            if not user_email and not user_geid:
                return {'result': 'either user_email or user_geid required.'}, 400
            # check user operation type
            if not operation_type in ['enable', 'restore', 'disable']:
                return {'result': 'operation {} is not allowed'.format(operation_type)}, 400

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
                return {'error_message': 'User not found'}, 403
            user_data = respon_user_information['result']
            user_current_status = user_data["status"]

            # validate operation type
            operation_validation = validate_operation_type(
                user_current_status, operation_type)
            if not operation_validation[0]:
                return {"error_message": "Invliad opertion type, User status: {}, Allowed operation types: {}"
                        .format(user_current_status, ", ".join(operation_validation[1]))}, 403

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
            # update user status
            user_data['status'] = user_status
            neo4j_client.update_user(user_data['id'], user_data)

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

                # update neo4j relations
                for project in linked_projects:
                    neo4j_client.update_relation(user_data['id'], project['neo4j_id'],
                                                 project['relation_name'], {'status': user_relationship_status})
            except Exception as e:
                return {"error_message": " relation update error: " + str(e), "project": project}, 500
            # entra operations
            try:
                if operation_type == "disable":
                    remove_from_vre_user_group(
                        user_data['email'], kc_cli, access_token)
                if operation_type == "enable":
                    enable_from_vre_user_group(
                        user_data['email'], kc_cli, access_token)
            except Exception as e:
                return {"error_message": "remove from vre_users group error: " + str(e)}, 500
            # sync keyclock
            kc_cli.sync_user_trigger()

            return {'result': {
                'user': user_data,
                'linked_projects': linked_projects,
            }}, 200

        except Exception as e:
            return {'error_message': "[Internal error]" + str(e)}, 500


def on_project_disable(email, project, kc_cli, access_token):
    ldap_user_grouppen = ConfigClass.LDAP_USER_GROUP
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


def remove_from_vre_user_group(email, kc_cli, access_token):
    # ldap user grouppen
    ldap_cli = LdapClient()
    ldap_cli.connect(ConfigClass.LDAP_USER_GROUP)
    ldap_users_gotten = ldap_cli.get_user_by_email(email)
    user_dn = ldap_users_gotten[0]
    user_entry = ldap_users_gotten[1]
    _logger.info("removed user dn: " + user_dn)
    remove_result = ldap_cli.remove_user_from_group(user_dn)
    ldap_cli.disconnect()


def enable_from_vre_user_group(email, kc_cli, access_token):
    # ldap user grouppen
    ldap_cli = LdapClient()
    ldap_cli.connect(ConfigClass.LDAP_USER_GROUP)
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
