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

from keycloak import KeycloakOpenID

from config import ConfigSettings


class OperationsUser:
    def __init__(self, client_id, realm_name, client_secret_key):
        self.keycloak_openid = KeycloakOpenID(
            server_url=ConfigSettings.KEYCLOAK_SERVER_URL,
            client_id=client_id,
            realm_name=realm_name,
            client_secret_key=client_secret_key,
        )
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
