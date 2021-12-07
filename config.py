import os
import requests
from requests.models import HTTPError
from pydantic import BaseSettings, Extra
from typing import Dict, Set, List, Any
from functools import lru_cache

SRV_NAMESPACE = os.environ.get("APP_NAME", "service_auth")
CONFIG_CENTER_ENABLED = os.environ.get("CONFIG_CENTER_ENABLED", "false")
CONFIG_CENTER_BASE_URL = os.environ.get("CONFIG_CENTER_BASE_URL", "NOT_SET")

def load_vault_settings(settings: BaseSettings) -> Dict[str, Any]:
    if CONFIG_CENTER_ENABLED == "false":
        return {}
    else:
        return vault_factory(CONFIG_CENTER_BASE_URL)

def vault_factory(config_center) -> dict:
    url = f"{config_center}/v1/utility/config/{SRV_NAMESPACE}"
    config_center_respon = requests.get(url)
    if config_center_respon.status_code != 200:
        raise HTTPError(config_center_respon.text)
    return config_center_respon.json()['result']


class Settings(BaseSettings):
    port: int = 5061
    host: str = "0.0.0.0"
    env: str = ""
    namespace: str = ""

    NEO4J_SERVICE: str
    EMAIL_SERVICE: str
    UTILITY_SERVICE: str

    EMAIL_SUPPORT: str = "jzhang@indocresearch.org"
    EMAIL_ADMIN: str = "cchen@indocresearch.org"
    EMAIL_HELPDESK: str = "helpdesk@vre"
    EMAIL_SUPPORT_PROD: str = "vre-support@charite.de"
    EMAIL_ADMIN_PROD: str = "vre-admin@charite.de"
    EMAIL_HELPDESK_PROD: str = "helpdesk@charite.de"

    # LDAP configs
    LDAP_URL: str
    LDAP_ADMIN_DN: str
    LDAP_ADMIN_SECRET: str
    LDAP_OU: str
    LDAP_DC1: str
    LDAP_DC2: str
    LDAP_objectclass: str
    LDAP_USER_GROUP: str

    # BFF RDS
    RDS_HOST: str
    RDS_PORT: str
    RDS_DBNAME: str
    RDS_USER: str
    RDS_PWD: str
    RDS_SCHEMA_DEFAULT: str

    # Keycloak config
    KEYCLOAK_VRE_CLIENT_ID: str
    KEYCLOAK_GRANT_TYPE: str
    KEYCLOAK_ID: str
    KEYCLOAK_SERVER_URL: str
    KEYCLOAK_VRE_SECRET: str

    # KEYCLOAK = vault['KEYCLOAK']
    KEYCLOAK_REALM: str = "vre"

    VRE_DOMAIN: str

    # Password reset config
    PASSWORD_RESET_EXPIRE_HOURS: int = 1
    PASSWORD_RESET_URL_PREFIX: str

    PASSWORD_REGEX: str = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\-_!%&/()=?*+#,.;])[A-Za-z\d\-_!%&/()=?*+#,.;]{11,30}$"

    TEST_PROJECT_CODE: str = "indoctestproject"
    TEST_PROJECT_ROLE: str = "collaborator"

    api_modules: List[str] = ["users"]
    JWT_AUTH_URL_RULE: None = None


    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = Extra.allow

        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            return (
                load_vault_settings,
                env_settings,
                init_settings,
                file_secret_settings,
            )
    

@lru_cache(1)
def get_settings():
    settings =  Settings()
    return settings

class ConfigClass(object):
    settings = get_settings()

    version = "0.1.0"
    env = settings.env
    disk_namespace = settings.namespace

    NEO4J_SERVICE = settings.NEO4J_SERVICE+"/v1/neo4j/"
    EMAIL_SERVICE = settings.EMAIL_SERVICE+"/v1/email"
    UTILITY_SERVICE = settings.UTILITY_SERVICE

    # Email addresses
    EMAIL_SUPPORT = settings.EMAIL_SUPPORT
    EMAIL_ADMIN = settings.EMAIL_ADMIN
    EMAIL_HELPDESK = settings.EMAIL_HELPDESK
    if env == 'charite':
        EMAIL_SUPPORT = settings.EMAIL_SUPPORT_PROD
        EMAIL_ADMIN = settings.EMAIL_ADMIN_PROD
        EMAIL_HELPDESK = settings.EMAIL_HELPDESK

    # LDAP configs
    LDAP_URL = settings.LDAP_URL + "/"
    LDAP_ADMIN_DN = settings.LDAP_ADMIN_DN
    LDAP_ADMIN_SECRET = settings.LDAP_ADMIN_SECRET
    LDAP_OU = settings.LDAP_OU
    LDAP_DC1 = settings.LDAP_DC1
    LDAP_DC2 = settings.LDAP_DC2
    LDAP_objectclass = settings.LDAP_objectclass
    LDAP_USER_GROUP = settings.LDAP_USER_GROUP

    # BFF RDS
    RDS_HOST = settings.RDS_HOST
    RDS_PORT = settings.RDS_PORT
    RDS_DBNAME = settings.RDS_DBNAME
    RDS_USER = settings.RDS_USER
    RDS_PWD = settings.RDS_PWD
    RDS_SCHEMA_DEFAULT = settings.RDS_SCHEMA_DEFAULT
    OPS_DB_URI = f"postgresql://{RDS_USER}:{RDS_PWD}@{RDS_HOST}/{RDS_DBNAME}"

    # Keycloak config
    KEYCLOAK_VRE_CLIENT_ID = settings.KEYCLOAK_VRE_CLIENT_ID
    KEYCLOAK_GRANT_TYPE = settings.KEYCLOAK_GRANT_TYPE
    KEYCLOAK_ID = settings.KEYCLOAK_ID
    KEYCLOAK_SERVER_URL = settings.KEYCLOAK_SERVER_URL
    KEYCLOAK_VRE_SECRET = settings.KEYCLOAK_VRE_SECRET
    KEYCLOAK = {
        "vre": ["kong", KEYCLOAK_VRE_SECRET]
    }

    # KEYCLOAK = vault['KEYCLOAK']
    KEYCLOAK_REALM = settings.KEYCLOAK_REALM

    VRE_DOMAIN = settings.VRE_DOMAIN

    # Password reset config
    PASSWORD_RESET_EXPIRE_HOURS = settings.PASSWORD_RESET_EXPIRE_HOURS
    PASSWORD_RESET_URL_PREFIX = settings.PASSWORD_RESET_URL_PREFIX

    PASSWORD_REGEX = settings.PASSWORD_REGEX

    TEST_PROJECT_CODE = settings.TEST_PROJECT_CODE
    TEST_PROJECT_ROLE = settings.TEST_PROJECT_ROLE

    api_modules = settings.api_modules
    JWT_AUTH_URL_RULE = settings.JWT_AUTH_URL_RULE