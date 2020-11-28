from keycloak import KeycloakAdmin
from config import ConfigClass


class OperationsAdmin:
    def __init__(
        self, 
        realm_name,
        server_url=ConfigClass.KEYCLOAK_SERVER_URL, 
        username=ConfigClass.ADMIN_USERNAME, 
        password=ConfigClass.ADMIN_PASSWORD,
        client_id=ConfigClass.KEYCLOAK['vre'][0],
        client_secret_key=ConfigClass.KEYCLOAK['vre'][1], 
        verify=True):
        self.keycloak_admin = KeycloakAdmin(
            server_url=server_url,
            client_id=client_id,
            client_secret_key=client_secret_key,
            realm_name=realm_name,
            verify = verify,
            username = username, 
            password = password)

    # create_user
    def create_user(
        self, 
        username, 
        password, 
        email, 
        firstname,
        lastname, 
        cred_type = "password",
        enabled = True):
        new_user = self.keycloak_admin.create_user(
            {
                "email": email,
                "username":username,
                "enabled": enabled,
                "firstName": firstname,
                "lastName": lastname,
                "credentials": [{"value": password,"type": cred_type}]
            }
        ) 
        return new_user
   
    # Delete User
    def delete_user(self,userid):
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
        res = self.keycloak_admin.set_user_password(userid, password, temporary)
        return res

    # Update user
    def update_user(self, userid, payload):
        res = self.keycloak_admin.update_user(user_id=userid, payload=payload)
        return res
