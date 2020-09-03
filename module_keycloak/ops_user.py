from keycloak import KeycloakOpenID
from config import ConfigClass

class OperationsUser:
    def __init__(self, client_id, realm_name, client_secret_key):
        self.keycloak_openid = KeycloakOpenID(
            server_url=ConfigClass.KEYCLOAK_SERVER_URL,
            client_id=client_id,
            realm_name=realm_name,
            client_secret_key=client_secret_key)
        self.config_well_know = self.keycloak_openid.well_know()
        self.token = ""

    # Get Token
    def get_token(self, username, password):
        self.token = self.keycloak_openid.token(username, password)
        return self.token
    
    # Get Userinfo
    def get_userinfo(self):
        userinfo = self.keycloak_openid.userinfo(self.token['access_token'])
        return userinfo

    # Refresh token
    def get_refresh_token(self, token):
        self.token = self.keycloak_openid.refresh_token(token)
        return self.token