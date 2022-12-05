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

import requests
from keycloak import KeycloakAdmin

from config import ConfigSettings


class OperationsAdmin:
    def __init__(
        self,
        realm_name,
        server_url=ConfigSettings.KEYCLOAK_SERVER_URL,
        client_id=ConfigSettings.KEYCLOAK_CLIENT_ID,
        client_secret_key=ConfigSettings.KEYCLOAK_SECRET,
        verify=True,
    ):
        self.keycloak_admin = KeycloakAdmin(
            server_url=server_url,
            client_id=client_id,
            client_secret_key=client_secret_key,
            realm_name=realm_name,
            verify=verify,
        )
        self.realm_name = realm_name
        self.token = self.keycloak_admin.token

    # create_user
    def create_user(
        self,
        username,
        password,
        email,
        firstname,
        lastname,
        cred_type='password',
        enabled=True,
    ):
        new_user = self.keycloak_admin.create_user(
            {
                "email": email,
                "username": username,
                "enabled": enabled,
                "firstName": firstname,
                "lastName": lastname,
                "credentials": [{"value": password, "type": cred_type}]
            }
        )
        return new_user

    # Delete User
    def delete_user(self, userid):
        response = self.keycloak_admin.delete_user(user_id=userid)
        return response

    # Get user ID from name
    def get_user_id(self, username):
        user_id = self.keycloak_admin.get_user_id(username)
        return user_id

    # Get User
    def get_user_info(self, userid):
        user = self.keycloak_admin.get_user(userid)
        return user

    # List all users
    def get_users(self, query):
        users = self.keycloak_admin.get_users()
        return users

    # Get user by email
    def get_user_by_email(self, email):
        users = self.keycloak_admin.get_users({"email": email})
        # Loop through search results and only return an exact match
        return next((user for user in users if user["email"] == email), None)

    # Set password for user
    def set_user_password(self, userid, password, temporary):
        res = self.keycloak_admin.set_user_password(
            userid, password, temporary)
        return res

    # Update user
    def update_user(self, userid, payload):
        res = self.keycloak_admin.update_user(user_id=userid, payload=payload)
        return res

    # Assign role
    def assign_user_role(self, userid, role_name):
        client_id = ConfigSettings.KEYCLOAK_CLIENT_ID
        realm_roles = self.keycloak_admin.get_realm_roles()
        find_role = [
            role for role in realm_roles if role['name'] == role_name][0]
        role_id = find_role['id']
        res = self.keycloak_admin.assign_realm_roles(
            client_id=client_id, user_id=userid, roles=[find_role])
        return res

    def sync_user_trigger(self):
        access_token = self.token['access_token']
        headers = {
            'Authorization': 'Bearer ' + access_token
        }
        url = f'{ConfigSettings.KEYCLOAK_SERVER_URL}admin/realms/{ConfigSettings.KEYCLOAK_REALM}/user-storage/{ConfigSettings.KEYCLOAK_ID}/sync?action=triggerChangedUsersSync'
        res = requests.post(url=url, headers=headers)
        return res

    def create_project_realm_roles(self, project_roles, code):
        access_token = self.token['access_token']
        headers = {
            'Authorization': 'Bearer ' + access_token
        }
        for role in project_roles:
            payload = {
                "name": "{}-{}".format(code, role)
            }
            url = f'{ConfigSettings.KEYCLOAK_SERVER_URL}admin/realms/{ConfigSettings.KEYCLOAK_REALM}/roles'
            res = requests.post(url=url, headers=headers, json=payload)
            if res.status_code != 201:
                return res
        return 'created'

    def delete_role_of_user(self, userid, role_name):
        access_token = self.token['access_token']
        headers = {
            'Authorization': 'Bearer ' + access_token
        }
        realm_roles = self.keycloak_admin.get_realm_roles()
        find_role = [
            role for role in realm_roles if role['name'] == role_name][0]
        url = f'{ConfigSettings.KEYCLOAK_SERVER_URL}admin/realms/{self.realm_name}/users/{userid}/role-mappings/realm'
        data = [
            find_role
        ]
        delete_res = requests.delete(url, json=data, headers=headers)
        return delete_res
