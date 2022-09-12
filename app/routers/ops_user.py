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

import json
import math
from datetime import datetime
from platform import platform

import httpx
import requests
from fastapi import APIRouter
from fastapi_utils import cbv
from keycloak import exceptions

from app.config import ConfigSettings
from app.models.api_response import APIResponse, EAPIResponseCode
from app.models.ops_user import (
    UserAuthPOST,
    UserProjectRoleDELETE,
    UserProjectRolePOST,
    UserTokenRefreshPOST,
)
from app.resources.error_handler import catch_internal
from app.resources.keycloak_api.ops_admin import OperationsAdmin
from app.resources.keycloak_api.ops_user import OperationsUser

router = APIRouter()
_API_TAG = 'v1/auth'
_API_NAMESPACE = 'api_auth'


@cbv.cbv(router)
class UserAuth:
    @router.post('/users/auth', tags=[_API_TAG], summary='make the user authentication and return the access token')
    @catch_internal(_API_NAMESPACE)
    async def post(self, data: UserAuthPOST):
        '''
        Summary:
            The api is using keycloak api to authenticate user and return
            the access_token and refresh_token. The user with disabled status
            cannot be login

        Payload:
            - username(string): The login string for user
            - password(string): login credential stored in keycloak

        Return:
            - access token
            - refresh token
        '''

        res = APIResponse()
        try:
            username = data.username
            password = data.password

            realm = ConfigSettings.KEYCLOAK_REALM
            client_id = ConfigSettings.KEYCLOAK_CLIENT_ID
            client_secret = ConfigSettings.KEYCLOAK_SECRET

            # log in
            user_client = OperationsUser(client_id, realm, client_secret)
            admin_client = OperationsAdmin(ConfigSettings.KEYCLOAK_REALM)
            token = user_client.get_token(username, password)
            # block the login if user is disabled
            user_info = admin_client.get_user_by_username(username)
            if user_info.get('attributes', {}).get('status', ['disabled']) == ['disabled']:
                raise exceptions.KeycloakAuthenticationError('User is disabled')

            # if authentication success update the user last login
            # time for displaying purpose
            user_id = user_info.get('id')
            last_login = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
            admin_client.update_user_attributes(user_id, {'last_login': last_login})

            res.result = token
            res.code = EAPIResponseCode.success
        except exceptions.KeycloakAuthenticationError as err:
            res.error_msg = str(err)
            res.code = EAPIResponseCode.unauthorized
        except exceptions.KeycloakGetError as err:
            res.error_msg = str(err)
            res.code = EAPIResponseCode.not_found
        except Exception as e:
            res.error_msg = f'User authentication failed : {e}'
            res.code = EAPIResponseCode.internal_error

        return res.json_response()


# might be used by skd
@cbv.cbv(router)
class UserRefresh:
    @router.post('/users/refresh', tags=[_API_TAG], summary='refresh the user token and issue a new one')
    @catch_internal(_API_NAMESPACE)
    async def post(self, data: UserTokenRefreshPOST):
        '''
        Summary:
            The api is using keycloak api to return a new refresh
            token for futher usage

        Payload:
            - refreshtoken(string): The expiring refresh token from
                same issuer/client in keycloak

        Return:
            - refresh token
        '''

        res = APIResponse()
        try:
            token = data.refreshtoken

            realm = ConfigSettings.KEYCLOAK_REALM
            client_id = ConfigSettings.KEYCLOAK_CLIENT_ID
            client_secret = ConfigSettings.KEYCLOAK_SECRET
            user_client = OperationsUser(client_id, realm, client_secret)
            token = user_client.get_refresh_token(token)

            res.result = token
            res.code = EAPIResponseCode.success
        except Exception as e:
            res.error_msg = f'Unable to get token : {e}'
            res.code = EAPIResponseCode.internal_error

        return res.json_response()


# this api is used by portal to add user into projects
@cbv.cbv(router)
class UserProjectRole:

    # TODO update to user_realm_role
    # also change the payload
    @router.post('/user/project-role', tags=[_API_TAG], summary='list the project role for given user')
    @catch_internal(_API_NAMESPACE)
    async def post(self, data: UserProjectRolePOST):
        '''
        Summary:
            The api is using keycloak api to add a user into existing
            keyclaok realm role

        Payload:
            - email(string): The unique email for the user to identiy
            - project_role(string): The target realm role

        Return:
            - 200 success
        '''

        res = APIResponse()
        email = data.email
        realm_role = data.project_role

        try:
            # use the admin client to grant the user realm role
            admin_client = OperationsAdmin(ConfigSettings.KEYCLOAK_REALM)
            user = admin_client.get_user_by_email(email)
            admin_client.assign_user_role(user['id'], realm_role)

            res.result = 'success'
            res.code = EAPIResponseCode.success

        except Exception as e:
            res.error_msg = f'Fail to add user to group: {e}'
            res.code = EAPIResponseCode.internal_error

        return res.json_response()

    @router.delete('/user/project-role', tags=[_API_TAG], summary='remove the project role for given user')
    @catch_internal(_API_NAMESPACE)
    async def delete(self, data: UserProjectRoleDELETE):
        '''
        Summary:
            The api is using keycloak api to add a user into existing
            keyclaok realm role

        Payload:
            - email(string): The unique email for the user to identiy
            - project_role(string): The target realm role

        Return:
            - 200 success
        '''

        res = APIResponse()
        realm = ConfigSettings.KEYCLOAK_REALM
        email = data.email
        project_role = data.project_role

        try:
            # use the admin client to remove the user realm role
            admin_client = OperationsAdmin(realm)
            user = admin_client.get_user_by_email(email)
            admin_client.delete_role_of_user(user['id'], project_role)

            res.result = 'success'
            res.code = EAPIResponseCode.success
        except Exception as e:
            res.error_msg = f'Fail to remove user from group: {e}'
            res.code = EAPIResponseCode.internal_error

        return res.json_response()


@cbv.cbv(router)
class UserList:
    @router.get('/users', tags=[_API_TAG], summary='list users from keycloak')
    @catch_internal(_API_NAMESPACE)
    async def get(
        self,
        username: str = None,
        email: str = None,
        page: int = 0,
        page_size: int = 10,
        status: str = None,
        role: str = None,
        order_by: str = None,
        order_type: str = 'asc',
    ):
        res = APIResponse()

        '''
        Summary:
            The api is used to the keycloak api and python to list all
            user under the platform.
            for now the api does not support the exact search and status check
            This will need to be wait until keycloak is upto v16
            The native api does not support join/sorting, so I temporary do them manually
            ALL the in memory sorting, searching, mapping are the temporary solution
            at the end, they will be sync to some primary db

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
            - user list
                - username
                - id
                - email
                - status
        '''

        try:
            admin_client = OperationsAdmin(ConfigSettings.KEYCLOAK_REALM)
            # get the total user count
            total_users = admin_client.get_user_count()

            # query = {
            #     "max": total_users,
            # }

            # NOTE HERE: the keycloak api does not support sorting
            # consider the amount of the user ~100. so I decide to use
            # python to do the sorting
            # if order_by:
            #     query.update({
            #         "first": 0,
            #         "max": 1000,
            #     })

            # admin_client = OperationsAdmin(ConfigSettings.KEYCLOAK_REALM)
            # # get the total user count
            # total_users = admin_client.get_user_count(**query)
            # get user detail\
            users = None
            if role == 'admin':
                users = admin_client.get_users_in_role('platform-admin')
            else:
                users = admin_client.get_all_users(max=total_users)
            user_list = [user for user in users if user.get('attributes', {}).get('status')]
            if username:
                user_list = [user for user in user_list if username in user.get('username')]
            if email:
                user_list = [user for user in user_list if email in user.get('email')]
            if status:
                user_list = [user for user in user_list if status in user.get('attributes', {}).get('status')]

            # here since the keycloak is NOT supporting sorting
            # manually sort the user by order_by and order_type
            if order_by:
                # since we use the snake case, here I will add a mapper to transfer
                # the camelcase for the sorting. only the first_name&last_name will
                # need the mapping, others keep the same
                order_by = {
                    'first_name': 'firstName',
                    'last_name': 'lastName',
                    'name': 'username',
                }.get(order_by, order_by)

                # field checking if orderby field does not exist return error
                if not (
                    order_by
                    in ['id', 'username', 'lastName', 'firstName', 'email', 'username', 'time_created', 'last_login']
                ):
                    res.error_msg = 'the order_by %s field does not exist' % (order_by)
                    res.code = EAPIResponseCode.bad_request
                    return res.json_response()

                # generate order lambda the special one is last_login_time
                # this is attached to attribute so we have to get one more step
                order_lambda = lambda user: user.get(order_by, '')
                if order_by == 'last_login':
                    order_lambda = lambda user: user.get('attributes').get('last_login', [''])[0]
                elif order_by == 'time_created':
                    order_lambda = lambda user: user.get('attributes').get('createTimestamp', [''])[0]

                user_list = sorted(user_list, key=order_lambda, reverse=True if order_type == 'desc' else False)

                # manually do the pagination
                # user_list = user_list[page*page_size:(page+1)*page_size]

            user_count = len(user_list)
            # finally filter out only return certain attributes
            # and do the pagination here
            user_list = [
                {
                    'id': user.get('id'),
                    'name': user.get('username'),
                    'username': user.get('username'),
                    'first_name': user.get('firstName'),
                    'last_name': user.get('lastName'),
                    'email': user.get('email'),
                    'time_created': datetime.fromtimestamp(user.get('createdTimestamp', 0) // 1000).strftime(
                        '%Y-%m-%dT%H:%M:%S'
                    ),
                    'last_login': user.get('attributes', {}).get('last_login', [None])[0],
                    'status': user.get('attributes', {}).get('status', ['disabled'])[0],
                }
                for user in user_list[page * page_size : (page + 1) * page_size]
            ]

            # also manually do the platform admin check
            platform_admins = [x.get('username') for x in admin_client.get_users_in_role('platform-admin')]
            # then do the looping over to match the return with platform admin
            # since the page is 10 and platform admin is ~10
            for user in user_list:
                if user.get('name') in platform_admins:
                    user.update({'role': 'admin'})
                else:
                    user.update({'role': 'member'})

            res.result = user_list
            res.total = user_count
            res.num_of_pages = math.ceil(user_count / page_size)
            res.page = page

        except Exception as e:
            res.error_msg = str(e)
            res.code = EAPIResponseCode.internal_error

        return res.json_response()
