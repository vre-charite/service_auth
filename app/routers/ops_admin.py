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

import math
from datetime import datetime

import httpx
from fastapi import APIRouter
from fastapi_utils import cbv
from keycloak import exceptions

from app.config import ConfigSettings
from app.models.api_response import APIResponse, EAPIResponseCode
from app.models.ops_admin import (
    RealmRolesPOST,
    UserGroupPOST,
    UserInRolePOST,
    UserOpsPOST,
)
from app.resources.error_handler import catch_internal
from app.resources.keycloak_api.ops_admin import OperationsAdmin

# from users import api


router = APIRouter()

_API_TAG = '/v1/admin'
_API_NAMESPACE = 'api_admin_ops'

# logger = SrvLoggerFactory(_API_NAMESPACE).get_logger()


@cbv.cbv(router)
class UserOps:
    @router.get('/admin/user', tags=[_API_TAG], summary='get user infomation by one of email, username, user_id')
    @catch_internal(_API_NAMESPACE)
    async def get(self, email: str = None, username: str = None, user_id: str = None):
        '''
        Summary:
            The api is used to the keycloak api to get user info
            including attributes

        Parameter:
            - email(string): the email from target user
            - username(string): the useranme from target user
            - user_id(string): the hash id from keycloak

        Return:
            - user information(dict)
        '''

        res = APIResponse()
        try:
            admin_client = OperationsAdmin(ConfigSettings.KEYCLOAK_REALM)

            # search the user by given input. Raise the exception
            # if ALL three inputs are missing
            user_info = None
            if email:
                user_info = admin_client.get_user_by_email(email)
            elif username:
                user_info = admin_client.get_user_by_username(username)
            elif user_id:
                user_info = admin_client.get_user_by_id(user_id)
            else:
                res.error_msg = 'One of email, username, user_id is mandetory'
                res.code = EAPIResponseCode.bad_request
                return res.json_response()

            # also update firstName, lastName to snake case
            # also make a duplicate field for name
            if user_info.get("firstName"):
                user_info.update({'first_name': user_info.pop('firstName')})
            else:
                user_info["first_name"] = ""
            if user_info.get("lastName"):
                user_info.update({'last_name': user_info.pop('lastName')})
            else:
                user_info["last_name"] = ""
            user_info.update({'name': user_info.get('username')})

            # the atttribute is return by list. but to simplify all
            # the api call chain, here will pickup the first one as value
            user_attribute = user_info.get('attributes', {})
            for x in user_attribute:
                user_attribute.update({x: user_attribute[x][0]})
            # by default the status will show as pending
            if not user_attribute.get('status', None):
                user_attribute.update({'status': 'pending'})
            user_info.update({'attributes': user_attribute})

            # also use the realm roles to match if user is platform admin
            realm_roles = admin_client.get_user_realm_roles(user_info.get('id'))
            platform_admin = [r for r in realm_roles if r.get('name') == 'platform-admin']
            if platform_admin:
                user_info.update({'role': 'admin'})
            else:
                user_info.update({'role': 'member'})

            res.result = user_info
            res.code = EAPIResponseCode.success
        except exceptions.KeycloakGetError:
            res.error_msg = 'user not found'
            res.code = EAPIResponseCode.not_found
        except Exception as e:
            res.error_msg = 'Fail to get user: ' + str(e)
            res.code = EAPIResponseCode.internal_error

        return res.json_response()

    @router.put(
        '/admin/user',
        tags=[_API_TAG],
        summary='currently only support update user attribute of \
                     last login_time and announcement',
    )
    @catch_internal(_API_NAMESPACE)
    async def put(self, data: UserOpsPOST):

        '''
        Summary:
            The api is used to the keycloak api to update user
            attributes

        Parameter:
            - last_login(bool optional): indicate if api need to update `last_login`
                attribute. The format will be "%Y-%m-%dT%H:%M:%S"
            - announcement(dict optional): the useranme from target user
                - project_code(string): the unique identifier of project
                - announcement_pk(string): the unique id for announcement
            - username(string): unique username in the keycloak

        Return:
            - user information(dict)
        '''

        res = APIResponse()

        last_login = data.last_login
        announcement = data.announcement
        username = data.username

        # one of the field is required
        if not last_login and not announcement:
            res.error_msg = 'last_login or announcement is required'
            res.code = EAPIResponseCode.bad_request
            return res.json_response()

        try:
            admin_client = OperationsAdmin(ConfigSettings.KEYCLOAK_REALM)
            user_id = admin_client.get_user_id(username)

            # update the attribute if payload is not None
            attri = {}
            # The format of string will be "%Y-%m-%dT%H:%M:%S"
            if last_login:
                last_login_str = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
                attri.update({'last_login': last_login_str})
            # update the announce as announcement_<project_code>: <announcement_pk>
            if announcement:
                attri.update({'announcement_' + announcement.project_code: announcement.announcement_pk})
            new_attribute = admin_client.update_user_attributes(user_id, attri)

            res.result = new_attribute
            res.code = EAPIResponseCode.success
        except exceptions.KeycloakGetError:
            res.error_msg = 'user not found'
            res.code = EAPIResponseCode.not_found
        except Exception as e:
            res.error_msg = str(e)
            res.code = EAPIResponseCode.internal_error

        return res.json_response()


# this api is used when create project
@cbv.cbv(router)
class UserGroup:
    @router.post('/admin/users/group', tags=[_API_TAG], summary='add user to existing group')
    @catch_internal(_API_NAMESPACE)
    async def post(self, data: UserGroupPOST):
        '''
        Summary:
            the api will add the user to the target keycloak group.
            create a new group if the target group is not exist

        Payload:
            - username(string): the useranme from keycloak
            - groupname(string): the unique groupname from keycloak

        Return:
            200 succuss
        '''

        res = APIResponse()
        try:
            username = data.username
            groupname = data.groupname

            operations_admin = OperationsAdmin(ConfigSettings.KEYCLOAK_REALM)
            user_id = operations_admin.get_user_id(username)
            group = operations_admin.get_group_by_name(groupname)
            # create the group in keycloak if not exist
            if not group:
                operations_admin.create_group(groupname)
                group = operations_admin.get_group_by_name(groupname)

            operations_admin.add_user_to_group(user_id, group['id'])
            res.result = 'success'
            res.code = EAPIResponseCode.success
        except Exception as e:
            # error_msg = f'UserGroup failed' + str(e)
            res.error_msg = f'UserGroup failed' + str(e)
            res.code = EAPIResponseCode.internal_error

        return res.json_response()

    @router.delete('/admin/users/group', tags=[_API_TAG], summary='add user to existing group')
    @catch_internal(_API_NAMESPACE)
    async def delete(self, username: str, groupname: str):
        '''
        Summary:
            the function will remove the target user from the
            given keycloak group

        Parameter:
            - username(string): the useranme from keycloak
            - groupname(string): the unique groupname from keycloak

        Return:
            200 succuss
        '''

        res = APIResponse()
        try:
            realm = ConfigSettings.KEYCLOAK_REALM

            # remove the user from target group
            operations_admin = OperationsAdmin(realm)
            user_id = operations_admin.get_user_id(username)
            group = operations_admin.get_group_by_name(groupname)
            operations_admin.remove_user_from_group(user_id, group['id'])

            res.result = 'success'
            res.code = EAPIResponseCode.success
        except Exception as e:
            res.error_msg = f'UserGroup delete failed' + str(e)
            res.code = EAPIResponseCode.internal_error

        return res.json_response()


# this api is used in project creation to create three new role in keycloak
@cbv.cbv(router)
class RealmRoles:
    # TODO might be move this api to users/realm-roles
    @router.get('/admin/users/realm-roles', tags=[_API_TAG], summary="get user's realm roles")
    @catch_internal(_API_NAMESPACE)
    async def get(self, username: str):
        '''
        Summary:
            The api is used to the keycloak api to fetch
            specific user's realm roles

        Parameter:
            - username(string): the useranme from target user

        Return:
            - realms infomation(list)
        '''

        res = APIResponse()
        try:
            # admin operator to get the user's realm roles
            operations_admin = OperationsAdmin(ConfigSettings.KEYCLOAK_REALM)
            user_id = operations_admin.get_user_by_username(username).get('id')

            res.result = operations_admin.get_user_realm_roles(user_id)
            res.code = EAPIResponseCode.success
        except Exception as e:
            res.error_msg = f'get realm roles in keycloak failed: {e}'
            res.code = EAPIResponseCode.internal_error

        return res.json_response()

    @router.post('/admin/users/realm-roles', tags=[_API_TAG], summary='add new realm roles in keycloak')
    @catch_internal(_API_NAMESPACE)
    async def post(self, data: RealmRolesPOST):
        '''
        Summary:
            The api is used to the keycloak api to create
            realm roles. The new name will be `<project_code>-
            <project_roles>`.

        Parameter:
            - project_roles(list): the list of roles to create in keycloak.
            - project_code(string): the unique code of project.

        Return:
            - 200 success
        '''

        res = APIResponse()
        try:
            project_roles = data.project_roles
            project_code = data.project_code
            # loop over the input roles and add user to it one by one
            operations_admin = OperationsAdmin(ConfigSettings.KEYCLOAK_REALM)
            keycloak_res = operations_admin.create_project_realm_roles(project_roles, project_code)

            res.result = 'success'
            res.code = EAPIResponseCode.success
        except Exception as e:
            res.error_msg = f'create realm roles in keycloak failed: {e}'
            res.code = EAPIResponseCode.internal_error

        return res.json_response()


@cbv.cbv(router)
class UserInRole:
    @router.post('/admin/roles/users', tags=[_API_TAG], summary='')
    @catch_internal(_API_NAMESPACE)
    async def post(self, data: UserInRolePOST):
        '''
        Summary:
            The api is used to the keycloak api and python to query
            user list under target realm roles.
            The native api does not support any seaching/join/sorting/pagination,
            so I temporary do them manually.
            ALL the in memory sorting, searching, mapping are the temporary solution
            at the end, they will be sync to some primary db.

        Parameter:
            - order_by(string optional): the field will be ordered by.
            - order_type(string optional): default=asc. support asc or desc.
            - page(int): default=0, the pagination to indicate current page.
            - page_size(int): default=10, the return user size.
            - username(string optional): if payload has username, the api will
                return all user contains target username.
            - email(string optional): if payload has email, the api will
                return all user contains target email.
            - status(string): not support yet

        Return:
            - 200 list of users
                - username
                - email
                - attributes
        '''

        res = APIResponse()
        order_by = data.order_by
        order_type = data.order_type
        page = data.page
        page_size = data.page_size
        username = data.username
        email = data.email
        status = data.status

        total_users = 0
        try:
            # intialize the keycloak admin to get token
            admin_client = OperationsAdmin(ConfigSettings.KEYCLOAK_REALM)
            user_list = []
            for role in data.role_names:
                user_in_role = admin_client.get_users_in_role(role)

                # then return only certain of attributes to frontend
                user_list += [
                    {
                        'id': user.get('id'),
                        'name': user.get('username'),
                        'username': user.get('username'),
                        'first_name': user.get('firstName'),
                        'last_name': user.get('lastName'),
                        'email': user.get('email'),
                        'permission': role.split('-')[-1],
                        'time_created': datetime.fromtimestamp(user.get('createdTimestamp', 0) // 1000).strftime(
                            '%Y-%m-%dT%H:%M:%S'
                        ),
                    }
                    for user in user_in_role
                ]

            # the keycloak native api doesnot support the searching
            # manually to do the searching since the users is about 10
            if username:
                user_list = [user for user in user_list if username in user.get('name')]
            if email:
                user_list = [user for user in user_list if email in user.get('email')]
            # if status:
            #     user_list = [user for user in user_list if status in user.get("attributes",{}).get("status", [])]

            # here since the keycloak is NOT supporting sorting
            # manually sort the user by order_by and order_type
            if order_by:

                # field checking if orderby field does not exist return error
                if not (
                    order_by
                    in ['id', 'name', 'first_name', 'last_name', 'email', 'permission', 'username', 'time_created']
                ):

                    res.error_msg = 'the order_by %s field does not exist' % (order_by)
                    res.code = EAPIResponseCode.bad_request
                    return res.json_response()

                order_lambda = lambda user: user.get(order_by, '')
                if order_by == 'time_created':
                    order_lambda = lambda user: user.get('attributes', {}).get('createTimestamp', [''])[0]
                user_list = sorted(user_list, key=order_lambda, reverse=True if order_type == 'desc' else False)

            # manually do the pagination
            total_users = len(user_list)
            user_list = user_list[page * page_size : (page + 1) * page_size]
            res.result = user_list
            res.total = total_users
            res.num_of_pages = math.ceil(total_users / page_size)
            res.page = page
        except Exception as e:
            res.error_msg = str(e)
            res.code = EAPIResponseCode.internal_error

        return res.json_response()
