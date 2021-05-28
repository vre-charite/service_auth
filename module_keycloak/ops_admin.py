from keycloak import KeycloakAdmin
from config import ConfigClass
import requests
import json


class OperationsAdmin:
    def __init__(
            self,
            realm_name,
            server_url=ConfigClass.KEYCLOAK_SERVER_URL,
            client_id=ConfigClass.KEYCLOAK['vre'][0],
            client_secret_key=ConfigClass.KEYCLOAK['vre'][1],
            verify=True):
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
            cred_type="password",
            enabled=True):
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
        client_id = ConfigClass.KEYCLOAK['vre'][0]
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
        url = ConfigClass.KEYCLOAK_SERVER_URL + 'admin/realms/vre/user-storage/{}/sync?action=triggerChangedUsersSync'.format(ConfigClass.KEYCLOAK_ID)
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
            url = ConfigClass.KEYCLOAK_SERVER_URL + 'admin/realms/vre/roles'
            res = requests.post(url=url, headers=headers, json=payload)
            if res.status_code != 201:
                return res
        return 'created'

    def delete_role_of_user(self, userid, role_name):
        access_token = self.token['access_token']
        headers = {
            'Authorization': 'Bearer ' + access_token
        }
        client_id = ConfigClass.KEYCLOAK['vre'][0]
        realm_roles = self.keycloak_admin.get_realm_roles()
        find_role = [
            role for role in realm_roles if role['name'] == role_name][0]
        url = ConfigClass.KEYCLOAK_SERVER_URL + \
            "admin/realms/{}/users/{}/role-mappings/realm" \
        .format(self.realm_name, userid)
        data = [
            find_role
        ]
        delete_res = requests.delete(url, json=data, headers=headers)
        return delete_res
