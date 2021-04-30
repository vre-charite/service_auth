import os
# os.environ['env'] = 'test'
class ConfigClass(object):
    env = os.environ.get('env')

    # Email Notify Service
    EMAIL_SERVICE = "http://notification.utility:5065/v1/email"
    NEO4J_SERVICE = "http://neo4j.utility:5062/v1/neo4j/"
    NEO4J_SERVICE_HOST = "http://neo4j.utility:5062"
    if env == "test":
        NEO4J_SERVICE_HOST = "http://10.3.7.216:5062"
        NEO4J_SERVICE = "http://10.3.7.216:5062/v1/neo4j/"
        EMAIL_SERVICE = "http://10.3.7.238:5065/v1/email"
    EMAIL_DEFAULT_NOTIFIER = "notification@vre"
    EMAIL_ADMIN_CONNECTION = "siteadmin.test@vre.com"

    # LDAP configs
    if env == "test":
        LDAP_URL = "ldap://10.3.50.101:389/"
        LDAP_ADMIN_DN = "svc-vre-ad@indoc.local"
        LDAP_ADMIN_SECRET = "indoc101!"
        LDAP_OU = "VRE-DEV"
        LDAP_USER_OU = "VRE-USER-DEV"
        LDAP_DC1 = "indoc"
        LDAP_DC2 = "local"
        LDAP_objectclass = "group"
        LDAP_USER_GROUP = "vre-users"
    elif env == "staging":
        LDAP_URL = "ldap://10.3.50.102:389/"
        LDAP_ADMIN_DN = "svc-vre-ad@indoc.local"
        LDAP_ADMIN_SECRET = "indoc101!"
        LDAP_OU = "VRE-STG"
        LDAP_USER_OU = "VRE-USER-STG"
        LDAP_DC1 = "indoc"
        LDAP_DC2 = "local"
        LDAP_objectclass = "group"
        LDAP_USER_GROUP = "vre-users"
    else:
        LDAP_URL = "ldap://10.3.50.101:389/"
        LDAP_ADMIN_DN = "svc-vre-ad@indoc.local"
        LDAP_ADMIN_SECRET = "indoc101!"
        LDAP_OU = "VRE-DEV"
        LDAP_USER_OU = "VRE-USER-DEV"
        LDAP_DC1 = "indoc"
        LDAP_DC2 = "local"
        LDAP_objectclass = "group"
        LDAP_USER_GROUP = "vre-users"


    # BFF RDS
    RDS_HOST = "opsdb.utility"
    RDS_PORT = "5432"
    RDS_DBNAME = "INDOC_VRE"
    RDS_USER = "postgres"
    RDS_PWD = "postgres"
    RDS_SCHEMA_DEFAULT = "indoc_vre"
    KEYCLOAK_ID = "f4b43b20-92f3-4b1b-bacc-3e191a206145"

    if env == "test":
        KEYCLOAK_SERVER_URL = "http://10.3.7.220/vre/auth/"
    elif env == "dev":
        KEYCLOAK_SERVER_URL = "http://10.3.7.220/vre/auth/"
    else:
        KEYCLOAK_SERVER_URL = "http://keycloak.utility:8080/vre/auth/"

    if env == "staging": 
        KEYCLOAK_VRE_SECRET = "6f595e33-3c8c-496f-b71e-af47f2e73667"
        KEYCLOAK = {
            "vre": ["kong", "6f595e33-3c8c-496f-b71e-af47f2e73667"]
        }
        PASSWORD_RESET_URL_PREFIX = "https://vre-staging.indocresearch.org"
        KEYCLOAK_ID = "87d2ce6c-6887-4e02-b2fd-1f07a4ff953c"
    elif env == "charite":
        KEYCLOAK_VRE_SECRET = "aeeddce5-b0cd-4a4c-9f6d-66b771692724"
        KEYCLOAK = {
            "vre": ["kong", "aeeddce5-b0cd-4a4c-9f6d-66b771692724"]
        }
        EMAIL_DEFAULT_NOTIFIER = "vre-support@charite.de"
        EMAIL_ADMIN_CONNECTION = "vre-support@charite.de"
        PASSWORD_RESET_URL_PREFIX = "https://vre.charite.de"
        RDS_USER = "indoc_vre"
        RDS_PWD = "opsdb-jrjmfa9svvC"  
        KEYCLOAK_ID = "aadfdc5b-e4e2-4675-9239-e2f9a10bdb50" 
        LDAP_URL = "ldap://charite.de/"
        LDAP_ADMIN_DN = "svc-vre-ad@CHARITE"
        LDAP_ADMIN_SECRET = "~*<whA\5PCnk%X<k"
        LDAP_OU = "VRE,OU=Charite-Zentrale-Anwendungen"
    else:
        KEYCLOAK_VRE_SECRET = "6f6b374b-1da9-4f77-b678-be48606e9905"
        KEYCLOAK = {
            "vre": ["kong", "6f6b374b-1da9-4f77-b678-be48606e9905"]
        }
        PASSWORD_RESET_URL_PREFIX = "http://10.3.7.220"

    PASSWORD_RESET_EXPIRE_HOURS = 1

    KEYCLOAK_VRE_CLIENT_ID = "kong"
    KEYCLOAK_GRANT_TYPE = "password"
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "admin"
    PASSWORD_REGEX = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\-_!%&/()=?*+#,.;])[A-Za-z\d\-_!%&/()=?*+#,.;]{11,30}$"

    api_modules = ["users"]
    JWT_AUTH_URL_RULE = None
