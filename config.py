import os
import requests
from requests.models import HTTPError

# os.environ['env']='test'

srv_namespace = "service_auth"
CONFIG_CENTER = "http://10.3.7.222:5062" \
    if os.environ.get('env') == "test" \
    else "http://common.utility:5062"


def vault_factory() -> dict:
    url = CONFIG_CENTER + \
        "/v1/utility/config/{}".format(srv_namespace)
    config_center_respon = requests.get(url)
    if config_center_respon.status_code != 200:
        raise HTTPError(config_center_respon.text)
    return config_center_respon.json()['result']


class ConfigClass(object):
    vault = vault_factory()
    env = os.environ.get('env')
    disk_namespace = os.environ.get('namespace')
    version = "0.1.0"
    NEO4J_SERVICE = vault['NEO4J_SERVICE']+"/v1/neo4j/"
    EMAIL_SERVICE = vault['EMAIL_SERVICE']+"/v1/email"

    EMAIL_DEFAULT_NOTIFIER = 'notification@vre'
    EMAIL_ADMIN_CONNECTION = 'siteadmin.test@vre.com'

    # LDAP configs
    LDAP_URL = vault['LDAP_URL']+"/"
    LDAP_ADMIN_DN = vault['LDAP_ADMIN_DN']
    LDAP_ADMIN_SECRET = vault['LDAP_ADMIN_SECRET']
    LDAP_OU = vault['LDAP_OU']
    LDAP_USER_OU = vault['LDAP_USER_OU']
    LDAP_DC1 = vault['LDAP_DC1']
    LDAP_DC2 = vault['LDAP_DC2']
    LDAP_objectclass = vault['LDAP_objectclass']
    LDAP_USER_GROUP = vault['LDAP_USER_GROUP']

    # BFF RDS
    RDS_HOST = vault['RDS_HOST']
    RDS_PORT = vault['RDS_PORT']
    RDS_DBNAME = vault['RDS_DBNAME']
    RDS_USER = vault['RDS_USER']
    RDS_PWD = vault['RDS_PWD']
    RDS_SCHEMA_DEFAULT = vault['RDS_SCHEMA_DEFAULT']
    OPS_DB_URI = f"postgresql://{RDS_USER}:{RDS_PWD}@{RDS_HOST}/{RDS_DBNAME}"

    # Keycloak config
    KEYCLOAK_VRE_CLIENT_ID = vault['KEYCLOAK_VRE_CLIENT_ID']
    KEYCLOAK_GRANT_TYPE = vault['KEYCLOAK_GRANT_TYPE']
    KEYCLOAK_ID = vault['KEYCLOAK_ID']
    KEYCLOAK_SERVER_URL = vault['KEYCLOAK_SERVER_URL']
    KEYCLOAK_VRE_SECRET = vault['KEYCLOAK_VRE_SECRET']
    KEYCLOAK = {
        "vre": ["kong", KEYCLOAK_VRE_SECRET]
    }

    # KEYCLOAK = vault['KEYCLOAK']
    KEYCLOAK_REALM = "vre"

    # Password reset config
    PASSWORD_RESET_EXPIRE_HOURS = 1
    PASSWORD_RESET_URL_PREFIX = vault['PASSWORD_RESET_URL_PREFIX']

    PASSWORD_REGEX = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\-_!%&/()=?*+#,.;])[A-Za-z\d\-_!%&/()=?*+#,.;]{11,30}$"

    api_modules = ["users"]
    JWT_AUTH_URL_RULE = None
