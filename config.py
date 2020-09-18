import os


class ConfigClass(object):
    KEYCLOAK_SERVER_URL = "http://keycloak.utility:8080/auth/"
    KEYCLOAK_TOKEN_URL = "http://keycloak.utility:8080/auth/realms/{}/protocol/openid-connect/token"
    KEYCLOAK_USER_URL = "http://keycloak.utility:8080/auth/admin/realms/{}/users"
    # KEYCLOAK_SERVER_URL = "http://10.3.7.223:8080/auth/"
    # KEYCLOAK_TOKEN_URL = "http://10.3.7.223:8080/auth/realms/{}/protocol/openid-connect/token"
    # KEYCLOAK_USER_URL = "http://10.3.7.223:8080/auth/admin/realms/{}/users"
    KEYCLOAK_VRE_CLIENT_ID = "kong"
    KEYCLOAK_GRANT_TYPE = "password"
    ADMIN_USERNAME = "stage-admin"
    ADMIN_PASSWORD = "admin"
    PASSWORD_REGEX = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@#$!%*?&^])[A-Za-z\d@#$!%*?&^]{8,16}$"
    NEO4J_SERVICE = "http://neo4j.utility:5062/v1/neo4j/"
    api_modules = ["users"]
    JWT_AUTH_URL_RULE = None
    env = os.environ.get('env')
    if env is None or env == 'charite':
        KEYCLOAK_VRE_SECRET = "aeeddce5-b0cd-4a4c-9f6d-66b771692724"
        KEYCLOAK = {
            "vre": ["kong", "aeeddce5-b0cd-4a4c-9f6d-66b771692724"]
        }
    elif env == 'staging':
        KEYCLOAK_VRE_SECRET = "6f595e33-3c8c-496f-b71e-af47f2e73667"
        KEYCLOAK = {
            "vre": ["kong", "6f595e33-3c8c-496f-b71e-af47f2e73667"]
        }
    else:
        KEYCLOAK_VRE_SECRET = "6f6b374b-1da9-4f77-b678-be48606e9905"
        KEYCLOAK = {
            "vre": ["kong", "6f6b374b-1da9-4f77-b678-be48606e9905"]
        }
