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

from common.services.logger_services.logger_factory_service import SrvLoggerFactory
from fastapi import APIRouter
from fastapi_utils import cbv

from app.config import ConfigSettings
from app.models.api_response import APIResponse, EAPIResponseCode
from app.models.user_account_management import (
    UserADGroupOperationsPUT,
    UserManagementV1PUT,
)
from app.resources.error_handler import catch_internal
from app.resources.keycloak_api.ops_admin import OperationsAdmin
from app.services.data_providers.ldap_client import LdapClient

router = APIRouter()

_API_TAG = 'v1/user/account'
_API_NAMESPACE = 'api_user_management'
_logger = SrvLoggerFactory(_API_NAMESPACE).get_logger()


@cbv.cbv(router)
class UserADGroupOperations:
    @router.put('/user/ad-group', tags=[_API_TAG], summary='add the target user to ad group')
    @catch_internal(_API_NAMESPACE)
    async def put(self, data: UserADGroupOperationsPUT):
        '''
        Summary:
            The api is used to directly add the user to ldap group.
            inside ldap the group name will be <prefix>-<group_code>

        Payload(UserManagementV1PUT):
            - operation_type(string): only accept remove or add
            - user_email(string): the target user email
            - group_code(string): the group code define by upperstream

        Return:
            200 updated
        '''

        _logger.info('Call API for user ad group operations')

        res = APIResponse()
        operation_type = data.operation_type
        group_code = data.group_code
        user_email = data.user_email

        try:
            ldap_cli = LdapClient()
            user_dn, _ = ldap_cli.get_user_by_email(user_email)
            # format the group_code with group dn
            group_dn = ldap_cli.format_group_dn(group_code)

            if operation_type == 'remove':
                ldap_cli.remove_user_from_group(user_dn, group_dn)
            elif operation_type == 'add':
                ldap_cli.add_user_to_group(user_dn, group_dn)

            res.result = '%s user %s from ad group' % (operation_type, user_email)
            res.code = EAPIResponseCode.success

        except Exception as e:
            res.error_msg = 'remove/add from users group error: ' + str(e)
            res.code = EAPIResponseCode.bad_request

        finally:
            ldap_cli.disconnect()

        return res.json_response()


# TODO change to user_id maybe
# also split to PUT and delete
@cbv.cbv(router)
class UserManagementV1:
    @router.put('/user/account', tags=[_API_TAG], summary='add the new user to ad')
    @catch_internal(_API_NAMESPACE)
    async def put(self, data: UserManagementV1PUT):
        '''
        Summary:
            The api is used to disable/enable users in portal. It is using
            keycloak api to setup the `status` of user attribute in keyloack
            to reflect disable or enable. user will be removed from ALL assigned
            realm role(all permissions)
            The ldap client is alse used to remove the user from corresponding DN
            in ldap

        Payload(UserManagementV1PUT):
            - operation_type(string): only accept disable or enable
            - user_email(string): the target user email

        Return:
            204 updated

        '''

        _logger.info('Call API for update user accounts')

        res = APIResponse()
        try:
            operation_type = data.operation_type
            user_email = data.user_email

            # check user operation type
            if not operation_type in ['enable', 'disable']:
                res.error_msg = 'operation {} is not allowed'.format(operation_type)
                res.code = EAPIResponseCode.bad_request
                return res.json_response()

            status = {
                'enable': 'active',
                'disable': 'disabled',
            }.get(operation_type)

            # first update the status by action
            kc_cli = OperationsAdmin(ConfigSettings.KEYCLOAK_REALM)
            user_id = kc_cli.get_user_by_email(user_email).get('id')
            kc_cli.update_user_attributes(user_id, {'status': status})

            if operation_type == 'disable':

                # keep the uma_authorization by default and remove
                # other roles from users. It will keep the uma_authorization
                # by default and remove other roles (remove the permission)
                realm_role = kc_cli.get_user_realm_roles(user_id)
                deleted_roles = [x for x in realm_role if x.get('name') != 'uma_authorization']
                kc_cli.remove_user_realm_roles(user_id, deleted_roles)

                ldap_cli = LdapClient()
                user_dn, ldap_info = ldap_cli.get_user_by_email(user_email)
                # remove all ldap start with <project>-* group except ConfigSettings.LDAP_USER_GROUP
                for x in ldap_info.get('memberOf'):
                    ldap_group = x.decode('utf-8')
                    if ConfigSettings.LDAP_USER_GROUP not in ldap_group and ldap_group.startswith(
                        'CN=' + ConfigSettings.LDAP_COMMON_NAME_PREFIX
                    ):
                        ldap_cli.remove_user_from_group(user_dn, ldap_group)

                ldap_cli.disconnect()

            res.result = '%s user %s' % (operation_type, user_email)
            res.code = EAPIResponseCode.success

        except Exception as e:
            _logger.error('[Internal error]' + str(e))
            res.error_msg = '[Internal error]' + str(e)
            res.code = EAPIResponseCode.internal_error

        return res.json_response()
