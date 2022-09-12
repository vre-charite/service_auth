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

import httpx
import requests
from keycloak import KeycloakAdmin, exceptions

from app.config import ConfigSettings
from app.models.api_response import EAPIResponseCode
from app.resources.error_handler import APIException


class OperationsAdmin:

    keycloak_admin: KeycloakAdmin

    def __init__(
        self,
        realm_name,
        server_url=ConfigSettings.KEYCLOAK_SERVER_URL,
        client_id=ConfigSettings.KEYCLOAK_CLIENT_ID,
        client_secret_key=ConfigSettings.KEYCLOAK_SECRET,
        verify=True,
    ):
        '''
        Summary:
            The initialization for the keycloak admin operation

        Parameter:
            - realm_name(string): the realm in keycloak
            - server_url(string optional): default=<value_in_config>
                keycloak endpoint
            - client_id(bool optional): default=<value_in_config>
                hash id for client in keycloak
            - client_secret_key(string optional): default=<value_in_config>
                 the credential for the target client
            - verify(bool optional): default=True last name for keyloack infomation

        Return:
            None
        '''

        self.keycloak_admin = KeycloakAdmin(
            server_url=server_url,
            client_id=client_id,
            client_secret_key=client_secret_key,
            realm_name=realm_name,
            verify=verify,
        )
        self.realm_name = realm_name
        self.token = self.keycloak_admin.token
        self.header = {'Authorization': 'Bearer ' + self.token.get('access_token'), 'Content-Type': 'application/json'}

    def get_user_id(self, username: str) -> str:
        '''
        Summary:
            The wraped for python keycloak client to get user id by username

        Parameter:
            - username(string): target username

        Return:
            - user_id(string): the hash id from keycloak
        '''

        user_id = self.keycloak_admin.get_user_id(username)
        return user_id

    def get_user_by_id(self, user_id: str) -> dict:
        '''
        Summary:
            The wraped for python keycloak client to get user infomation
            by id

        Parameter:
            - userid(string): the hash id from keycloak

        Return:
            - user(dict): the user infomation from keycloak
        '''

        user = self.keycloak_admin.get_user(user_id)
        return user

    def get_user_by_email(self, email: str) -> dict:
        '''
        Summary:
            The wraped for python keycloak client to get user infomation
            by email

        Parameter:
            - email(string): the email for target user

        Return:
            - user(dict): the user infomation from keycloak
        '''

        users = self.keycloak_admin.get_users({'email': email})
        # Loop through search results and only return an exact match
        return next((user for user in users if user['email'] == email), None)

    def get_user_by_username(self, username: str) -> dict:
        '''
        Summary:
            The wraped for python keycloak client to get user infomation
            by email

        Parameter:
            - email(string): the email for target user

        Return:
            - user(dict): the user infomation from keycloak
        '''

        user_id = self.keycloak_admin.get_user_id(username)
        user = self.keycloak_admin.get_user(user_id)
        # Loop through search results and only return an exact match
        return user

    def update_user_attributes(self, user_id: str, new_attributes: dict) -> dict:
        '''
        Summary:
            the function will use keycloak api to update the user attribute
            NOTE HERE: the api update attribute will overwrite existing one.
            so logic now will fetch the existing attributes and update it
            before the request

        Parameter:
            - user_id(string): the user id (hash) in keycloak
            - new_attributes(dictionary): the new attributes that will be ADD
                to the user

        Return:
            newly updated attribute
        '''

        # get user info and update the new attribute to existing
        user_info = self.keycloak_admin.get_user(user_id)
        attri = user_info.get('attributes', {})
        attri.update(new_attributes)

        with httpx.Client() as client:
            api = (
                ConfigSettings.KEYCLOAK_SERVER_URL
                + 'admin/realms/'
                + ConfigSettings.KEYCLOAK_REALM
                + '/users/'
                + user_id
            )
            api_res = client.put(api, headers=self.header, json={'attributes': attri})
            # return check if fail raise the error
            if api_res.status_code != 204:
                raise Exception('Fail to update user attributes: ' + str(api_res.__dict__))

        return new_attributes

    def get_all_users(
        self, username: str = None, email: str = None, first: int = 0, max: int = 1000, q: str = ''
    ) -> list:
        '''
        Summary:
            The wraped for keycloak api to get all user as
            pagination list that matching the filter condtion

        Parameter:
            - username(string): if payload has username, the api will
                return all user contains target username.
            - email(string): if payload has email, the api will
                return all user contains target email.
            - first(int): the pagination to skip <first> user.
            - max(int): the return size of list.
            - q(string): searching the customized user attribute

        Return:
            - users(list): the user infomation from keycloak
        '''

        query = {
            'username': username,
            'email': email,
            'first': first,
            'max': max,
            'q': q,
        }

        api = ConfigSettings.KEYCLOAK_SERVER_URL + 'admin/realms/' + ConfigSettings.KEYCLOAK_REALM + '/users'
        with httpx.Client() as client:
            api_res = client.get(api, headers=self.header, params=query)
            # return check if fail raise the error
            if api_res.status_code != 200:
                raise Exception('Fail to get all user: ' + str(api_res.__dict__))

        return api_res.json()

    def get_user_count(
        self, username: str = None, email: str = None, first: int = 0, max: int = 1000, q: str = ''
    ) -> int:
        '''
        Summary:
            The wraped for keycloak api to get the user count that
            matching the filter condtion

        Parameter:
            - username(string): if payload has username, the api will
                return all user contains target username.
            - email(string): if payload has email, the api will
                return all user contains target email.
            - first(int): the pagination to skip <first> user.
            - max(int): the return size of list.
            - q(string): searching the customized user attribute

        Return:
            - user_count(int)
        '''

        query = {
            'username': username,
            'email': email,
            'first': first,
            'max': max,
            # "exact": 'true'
            'q': q,
        }

        api = ConfigSettings.KEYCLOAK_SERVER_URL + 'admin/realms/' + ConfigSettings.KEYCLOAK_REALM + '/users/count'
        with httpx.Client() as client:
            api_res = client.get(api, headers=self.header, params=query)
            # return check if fail raise the error
            if api_res.status_code != 200:
                raise Exception('Fail to get user count: ' + str(api_res.__dict__))
        return api_res.json()

    # the realm role operations

    def assign_user_role(self, user_id, role_name) -> dict:
        '''
        Summary:
            the function will assign the user to target realm role in keycloak

        Parameter:
            - user_id(string): the user id (hash) in keycloak
            - role_name(string): The new role name that will assign to user

        Return:
            dict
        '''

        client_id = ConfigSettings.KEYCLOAK_CLIENT_ID
        realm_roles = self.keycloak_admin.get_realm_roles()
        # pick out the role we wnat to assign
        find_role = [role for role in realm_roles if role['name'] == role_name]
        if len(find_role) == 0:
            raise Exception('Failed to find the role')

        res = self.keycloak_admin.assign_realm_roles(client_id=client_id, user_id=user_id, roles=find_role)
        return res

    def get_user_realm_roles(self, user_id: str) -> list:
        '''
        Summary:
            the function will use the keycloak native api to fecth the
            realm role from user id

        Parameter:
            - user_id(string): the user id (hash) in keycloak

        Return:
            list of the realm roles
        '''

        with httpx.Client() as client:
            api = (
                ConfigSettings.KEYCLOAK_SERVER_URL
                + 'admin/realms/'
                + ConfigSettings.KEYCLOAK_REALM
                + '/users/'
                + user_id
                + '/role-mappings/realm'
            )
            api_res = client.get(api, headers=self.header)
            # return check if fail raise the error
            if api_res.status_code != 200:
                raise Exception('Fail to get user realm roles: ' + str(api_res.__dict__))

        return api_res.json()

    def remove_user_realm_roles(self, user_id: str, realm_roles: list) -> None:
        '''
        Summary:
            the function will use the keycloak native api to fecth the
            realm role from user id

        Parameter:
            - user_id(string): the user id (hash) in keycloak

        Return:
            list of the realm roles
        '''

        # remove user from all existing role (remove the permission)
        with httpx.Client() as client:
            api = (
                ConfigSettings.KEYCLOAK_SERVER_URL
                + 'admin/realms/'
                + ConfigSettings.KEYCLOAK_REALM
                + '/users/'
                + user_id
                + '/role-mappings/realm'
            )
            # the httpx.delete deos not suppor the payload so I switch to genetic method
            request = httpx.Request('DELETE', api, headers=self.header, json=realm_roles)
            api_res = client.send(request)
            # return check if fail raise the error
            if api_res.status_code != 200:
                raise Exception('Fail to remove user from realm: ' + str(api_res.__dict__))

    def create_project_realm_roles(self, project_roles: list, code: str) -> None:
        '''
        Summary:
            the function will use the native the keycloak api to create
            a realm role

        Parameter:
            - project_roles(list): the list of project roles will be admin,
                collaborator, contributor
            - code(string): The project code

        Return:
            None
        '''

        for role in project_roles:
            payload = {'name': '{}-{}'.format(code, role)}
            url = f'{ConfigSettings.KEYCLOAK_SERVER_URL}admin/realms/{ConfigSettings.KEYCLOAK_REALM}/roles'
            res = requests.post(url=url, headers=self.header, json=payload)
            if res.status_code != 201:
                raise Exception('Fail to create new role' + str(res.__dict__))
        return res

    def delete_role_of_user(self, user_id: str, role_name: str):
        '''
        Summary:
            the function will use the native the keycloak api to remove
            user from target a realm role

        Parameter:
            - user_id(string): the hash id from keycloak
            - role_name(string): the role name from keycloak

        Return:
            None
        '''

        realm_roles = self.keycloak_admin.get_realm_roles()
        find_role = [role for role in realm_roles if role['name'] == role_name]

        # raise the error if user does not have target role
        if len(find_role) == 0:
            raise Exception('User %s does not have role %s' % (user_id, role_name))

        url = f'{ConfigSettings.KEYCLOAK_SERVER_URL}admin/realms/{self.realm_name}/users/{user_id}/role-mappings/realm'
        delete_res = requests.delete(url, json=find_role, headers=self.header)
        return delete_res

    def get_users_in_role(self, role_name: str) -> list:
        '''
        Summary:
            the function will return the all users under target
            role name

        Parameter:
            - role_name(string): the role name from keycloak

        Return:
            list of user:
                - username
                - attributes
                - email
        '''

        with httpx.Client() as client:
            api = (
                ConfigSettings.KEYCLOAK_SERVER_URL
                + 'admin/realms/'
                + ConfigSettings.KEYCLOAK_REALM
                + '/roles/'
                + role_name
                + '/users'
            )
            api_res = client.get(api, headers=self.header)

            if api_res.status_code == 404:
                raise Exception('Role %s is not found' % role_name)

        return api_res.json()

    def sync_user_trigger(self):
        access_token = self.token['access_token']
        url = f'{ConfigSettings.KEYCLOAK_SERVER_URL}admin/realms/{ConfigSettings.KEYCLOAK_REALM}/user-storage/{ConfigSettings.KEYCLOAK_ID}/sync?action=triggerChangedUsersSync'
        res = requests.post(url=url, headers=self.header)
        return res

    # the group operation

    def get_group_by_name(self, group_name: str) -> dict:
        '''
        Summary:
            the function will get the group from keycloak

        Parameter:
            - group_name(string): the group name from keycloak

        Return:
            group inforamtion(dict)
        '''
        group_info = self.keycloak_admin.get_group_by_path(f'/{group_name}')
        return group_info

    def create_group(self, group_name: str) -> None:
        '''
        Summary:
            the function will create new group in keycloak

        Parameter:
            - group_name(string): the group name from keycloak

        Return:
            None
        '''

        group_dict = {'name': group_name}
        self.keycloak_admin.create_group(group_dict)
        return None

    def add_user_to_group(self, user_id: str, group_id: str) -> None:
        '''
        Summary:
            the function will create new group in keycloak

        Parameter:
            - user_id(string): the user id from keycloak
            - group_id(string): the group id from keycloak

        Return:
            None
        '''

        self.keycloak_admin.group_user_add(user_id, group_id)
        return None

    def remove_user_from_group(self, user_id: str, group_id: str) -> None:
        '''
        Summary:
            the function will create new group in keycloak

        Parameter:
            - user_id(string): the user id from keycloak
            - group_id(string): the group id from keycloak

        Return:
            None
        '''
        self.keycloak_admin.group_user_remove(user_id, group_id)
        return None

    def check_user_exists(self, email: str) -> bool:
        try:
            self.get_user_by_email(email)
            return True
        except exceptions.KeycloakGetError:
            return False
