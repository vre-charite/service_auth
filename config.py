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

from functools import lru_cache
from typing import Any
from typing import Dict
from typing import Optional

from common import VaultClient
from pydantic import BaseModel
from pydantic import BaseSettings
from pydantic import Extra


class VaultConfig(BaseSettings):
    """Store vault related configuration."""

    APP_NAME: str = 'service_auth'
    CONFIG_CENTER_ENABLED: bool = False

    VAULT_URL: Optional[str]
    VAULT_CRT: Optional[str]
    VAULT_TOKEN: Optional[str]

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


def load_vault_settings(settings: BaseSettings) -> Dict[str, Any]:
    config = VaultConfig()

    if not config.CONFIG_CENTER_ENABLED:
        return {}

    client = VaultClient(config.VAULT_URL, config.VAULT_CRT, config.VAULT_TOKEN)
    return client.get_from_vault(config.APP_NAME)


class FlaskConfig(BaseModel):
    """Store flask related configuration."""

    JWT_AUTH_URL_RULE: Optional[str] = None


class Settings(BaseSettings):
    """Store service configuration settings."""

    APP_NAME: str = 'service_auth'
    VERSION: str = '0.1.0'
    PORT: int = 5061
    HOST: str = '0.0.0.0'
    env: str = ''
    namespace: str = ''

    NEO4J_SERVICE: str
    EMAIL_SERVICE: str
    UTILITY_SERVICE: str

    EMAIL_SUPPORT: str
    EMAIL_ADMIN: str
    EMAIL_HELPDESK: str

    # LDAP configs
    LDAP_URL: str
    LDAP_ADMIN_DN: str
    LDAP_ADMIN_SECRET: str
    LDAP_OU: str
    LDAP_DC1: str
    LDAP_DC2: str
    LDAP_objectclass: str
    LDAP_USER_GROUP: str
    LDAP_COMMON_NAME_PREFIX: str

    # BFF RDS
    RDS_HOST: str
    RDS_PORT: str
    RDS_DBNAME: str
    RDS_USER: str
    RDS_PWD: str
    RDS_SCHEMA_DEFAULT: str
    RDS_DB_URI: str

    # Keycloak config
    KEYCLOAK_GRANT_TYPE: str
    KEYCLOAK_ID: str
    KEYCLOAK_SERVER_URL: str
    KEYCLOAK_CLIENT_ID: str
    KEYCLOAK_SECRET: str
    KEYCLOAK_REALM: str

    DOMAIN_NAME: str
    START_PATH: str
    GUIDE_PATH: str

    TEST_PROJECT_CODE: str = 'test-project-code'
    TEST_PROJECT_ROLE: str = 'collaborator'

    OPEN_TELEMETRY_ENABLED: bool = False
    OPEN_TELEMETRY_HOST: str = '127.0.0.1'
    OPEN_TELEMETRY_PORT: int = 6831

    FLASK: FlaskConfig = FlaskConfig()

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = Extra.allow

        @classmethod
        def customise_sources(cls, init_settings, env_settings, file_secret_settings):
            return env_settings, load_vault_settings, init_settings, file_secret_settings

    def __init__(self, *args: Any, **kwds: Any) -> None:
        super().__init__(*args, **kwds)

        self.NEO4J_SERVICE += '/v1/neo4j/'
        self.EMAIL_SERVICE += '/v1/email'


@lru_cache(1)
def get_settings():
    settings = Settings()
    return settings


ConfigSettings = get_settings()
