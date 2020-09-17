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
        KEYCLOAK_VRE_SECRET = "9f06a414-8e5f-472b-a161-7b21fcd30078"
        KEYCLOAK = {
            "vre": ["kong", "9f06a414-8e5f-472b-a161-7b21fcd30078"]
        }
    elif env == 'staging':
        KEYCLOAK_VRE_SECRET = "17b2f5a7-64ba-4ab3-a392-d497c6d50848"
        KEYCLOAK = {
            "vre": ["kong", "17b2f5a7-64ba-4ab3-a392-d497c6d50848"]
        }
    else:
        KEYCLOAK_VRE_SECRET = "d2f56cf0-120d-499a-b525-9f26f7a0274f"
        KEYCLOAK = {
            "vre": ["kong", "d2f56cf0-120d-499a-b525-9f26f7a0274f"]
        }
