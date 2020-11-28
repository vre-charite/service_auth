import os


class ConfigClass(object):
    env = os.environ.get('env')
    KEYCLOAK_SERVER_URL = "http://keycloak.utility:8080/vre/auth/"
    KEYCLOAK_TOKEN_URL = "http://keycloak.utility:8080/vre/auth/realms/{}/protocol/openid-connect/token"
    KEYCLOAK_USER_URL = "http://keycloak.utility:8080/vre/auth/admin/realms/{}/users"
    if env == "test":
        KEYCLOAK_SERVER_URL = "http://10.3.7.223:8080/vre/auth/"
        KEYCLOAK_TOKEN_URL = "http://10.3.7.223:8080/vre/auth/realms/{}/protocol/openid-connect/token"
        KEYCLOAK_USER_URL = "http://10.3.7.223:8080/vre/auth/admin/realms/{}/users"
    KEYCLOAK_VRE_CLIENT_ID = "kong"
    KEYCLOAK_GRANT_TYPE = "password"
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "admin"
    PASSWORD_REGEX = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\-_!%&/()=?*+#,.;])[A-Za-z\d\-_!%&/()=?*+#,.;]{11,30}$"
    NEO4J_SERVICE = "http://neo4j.utility:5062/v1/neo4j/"
    api_modules = ["users"]
    JWT_AUTH_URL_RULE = None
    
    # Email Notify Service
    EMAIL_SERVICE = "http://notification.utility:5065/v1/email"
    if env == "test":
        EMAIL_SERVICE = "http://10.3.7.238:5065/v1/email"
    EMAIL_DEFAULT_NOTIFIER = "notification@vre"
    EMAIL_ADMIN_CONNECTION = "siteadmin.test@vre.com"
    if env == 'charite':
         # Config Email Service in charite
        EMAIL_DEFAULT_NOTIFIER = "vre-support@charite.de"
        EMAIL_ADMIN_CONNECTION = "vre-support@charite.de"
        # PASSWORD_RESET_URL_PREFIX = "http://10.32.42.226/vre/"
        PASSWORD_RESET_URL_PREFIX = "https://vre.charite.de/vre/"
    elif env == "staging":
        PASSWORD_RESET_URL_PREFIX = "https://nx.indocresearch.org/vre/"
    else:
        PASSWORD_RESET_URL_PREFIX = "http://10.3.7.220/vre/"
    PASSWORD_RESET_EXPIRE_HOURS = 1

    # BFF RDS
    RDS_HOST = "opsdb.utility"
    RDS_PORT = "5432"
    RDS_DBNAME = "INDOC_VRE"
    RDS_USER = "postgres"
    RDS_PWD = "postgres"
    if env == 'charite':
        RDS_USER = "indoc_vre"
        RDS_PWD = "opsdb-jrjmfa9svvC"
    RDS_SCHEMA_DEFAULT = "indoc_vre"

    if env == 'charite':
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
