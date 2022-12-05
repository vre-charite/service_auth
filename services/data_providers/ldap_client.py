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

import ldap
from common.services.logger_services.logger_factory_service import SrvLoggerFactory

from config import ConfigSettings

_logger = SrvLoggerFactory('ldap client').get_logger()


class LdapClient:
    """LdapClient"""

    def connect(self, dn_code):
        _logger.debug(dn_code)
        '''
        need build connection before using ldap client
        '''
        ldap.set_option(ldap.OPT_REFERRALS, ldap.OPT_OFF)
        self.conn = ldap.initialize(ConfigSettings.LDAP_URL)
        self.dn = ','.join([
            f'cn={ConfigSettings.LDAP_COMMON_NAME_PREFIX}-{dn_code}',
            f'ou=Gruppen',
            f'ou={ConfigSettings.LDAP_OU}',
            f'dc={ConfigSettings.LDAP_DC1}',
            f'dc={ConfigSettings.LDAP_DC2}',
        ])
        _logger.info(self.dn)
        self.objectclass = [ConfigSettings.LDAP_objectclass.encode('utf-8')]
        self.conn.simple_bind_s(ConfigSettings.LDAP_ADMIN_DN, ConfigSettings.LDAP_ADMIN_SECRET)

    def disconnect(self):
        self.conn.unbind_s()

    def add_user_to_group(self, user_dn):
        _logger.info("add user: " + user_dn)
        _logger.info("add user from group dn: " + self.dn)
        operation_list = [(ldap.MOD_ADD, 'member', [user_dn.encode('utf-8')])]
        try:
            res = self.conn.modify_s(
                self.dn,
                operation_list
            )
        except Exception as e:
            _logger.error(str(e))
            raise e
        _logger.info("response from AD: " + ','.join(str(x) for x in res))
        return res

    def remove_user_from_group(self, user_dn):
        _logger.info("removed user: " + user_dn)
        _logger.info("remove user from group dn: " + self.dn)
        operation_list = [(ldap.MOD_DELETE, 'member', [user_dn.encode('utf-8')])]

        res = self.conn.modify_s(
            self.dn,
            operation_list
        )
        return res

    def get_all_users(self):
        '''
        Return ldap user dn list
        '''
        _logger.info("remove user from group dn: " + self.dn)
        _logger.info("search users dn: " + "dc={},dc={}".format(ConfigSettings.LDAP_DC1, ConfigSettings.LDAP_DC2))
        users = self.conn.search_s(
            "dc={},dc={}".format(ConfigSettings.LDAP_DC1, ConfigSettings.LDAP_DC2),
            ldap.SCOPE_SUBTREE,
            '(objectClass=user)'
        )
        _logger.info("number of users found: " + str(len(users)))
        return users

    def get_user_in_ldapsever_by_email(self, email):
        '''
        Return ldap user dn list
        '''
        users = self.conn.search_s(
            "dc={},dc={}".format(ConfigSettings.LDAP_DC1, ConfigSettings.LDAP_DC2),
            ldap.SCOPE_SUBTREE,
            '(&(objectClass=user)(mail={}))'.format(email)
        )
        return users

    def get_user_by_email(self, email):
        '''
        return tuple(user_dn, entry)
        '''
        users_all = self.get_user_in_ldapsever_by_email(email)
        user_found = None
        for user_dn, entry in users_all:
            if 'mail' in entry:
                decoded_email = entry['mail'][0].decode("utf-8")
                if decoded_email == email:
                    user_found = (user_dn, entry)
        _logger.info("found user by email: " + str(user_found))
        if not user_found:
            raise Exception('get_user_by_email error: User not found on AD: ' + email)
        return user_found

    def get_user_by_username(self, username):
        '''
        Return ldap user dn by given username
        '''
        users = self.conn.search_s(
            "dc={},dc={}".format(ConfigSettings.LDAP_DC1, ConfigSettings.LDAP_DC2),
            ldap.SCOPE_SUBTREE,
            f'(&(objectClass=user)(sAMAccountName={username}))'
        )
        user_found = None
        for user_dn, entry in users:
            if 'sAMAccountName' in entry:
                decoded_username = entry['sAMAccountName'][0].decode("utf-8")
                if decoded_username == username:
                    user_found = (user_dn, entry)
        _logger.info("found user by username: " + str(user_found))
        if not user_found:
            return None, None
        return user_found
