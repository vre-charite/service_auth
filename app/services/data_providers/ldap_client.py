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

from typing import Tuple

import ldap
from common.services.logger_services.logger_factory_service import SrvLoggerFactory

from app.config import ConfigSettings

_logger = SrvLoggerFactory('ldap client').get_logger()


class LdapClient:
    """LdapClient."""

    def __init__(self) -> None:
        ldap.set_option(ldap.OPT_REFERRALS, ldap.OPT_OFF)
        self.connect()

    def connect(self) -> None:
        '''
        Summary:
            Setup the connection with ldap by the configure file

        Return:
            None
        '''
        self.conn = ldap.initialize(ConfigSettings.LDAP_URL)
        self.objectclass = [ConfigSettings.LDAP_objectclass.encode('utf-8')]
        self.conn.simple_bind_s(ConfigSettings.LDAP_ADMIN_DN, ConfigSettings.LDAP_ADMIN_SECRET)

    def disconnect(self) -> None:
        '''
        Summary:
            disconnect from ldap

        Return:
            None
        '''
        self.conn.unbind_s()

    def format_group_dn(self, group_name: str) -> str:
        '''
        Summary:
            format the dn as  cn=<prefix>-<group_name>, ou=Gruppen, ou=<>, dc=<>, dc=<>

        Parameter:
            group_name(string): the group name that will be added
                into AD

        Return:
            formated dn name(string)
        '''
        group_dn = ','.join(
            [
                f'cn={ConfigSettings.LDAP_COMMON_NAME_PREFIX}-{group_name}',
                'ou=Gruppen',
                f'ou={ConfigSettings.LDAP_OU}',
                f'dc={ConfigSettings.LDAP_DC1}',
                f'dc={ConfigSettings.LDAP_DC2}',
            ]
        )

        return group_dn

    def add_user_to_group(self, user_dn: str, group_dn: str) -> str:
        '''
        Summary:
            adding the user to target group_dn. Note here,
            there group_dn is the result from format_group_dn function

        Parameter:
            user_dn(string): formated user dn
            user_dn(group_dn): formated group dn

        Return:
            formated dn name(string)
        '''

        _logger.info('add user: ' + user_dn)
        _logger.info('add user from group dn: ' + group_dn)
        try:
            operation_list = [(ldap.MOD_ADD, 'member', [user_dn.encode('utf-8')])]
            res = self.conn.modify_s(group_dn, operation_list)
        except ldap.ALREADY_EXISTS as e:
            _logger.info('Already in group skipping group add:' + group_dn)
            return "conflict"
        return "success"

    def remove_user_from_group(self, user_dn: str, group_dn: str) -> dict:
        '''
        Summary:
            remove the user to target group_dn. Note here,
            there group_dn/user_dn are the result from format_group_dn function

        Parameter:
            user_dn(string): formated user dn
            user_dn(group_dn): formated group dn

        Return:
            formated dn name(string)
        '''
        _logger.info('removed user: ' + user_dn)
        _logger.info('remove user from group dn: ' + group_dn)
        operation_list = [(ldap.MOD_DELETE, 'member', [user_dn.encode('utf-8')])]
        res = self.conn.modify_s(group_dn, operation_list)
        return res

    def get_user_by_email(self, email: str) -> Tuple[str, dict]:
        '''
        Summary:
            get the user infomation in ldap by email

        Parameter:
            email(string): user email in ldap

        Return:
            user_dn(string): user dn in ldap
            user_info(dict): the rest infomation in user eg. group
        '''
        users_all = self.conn.search_s(
            'dc={},dc={}'.format(ConfigSettings.LDAP_DC1, ConfigSettings.LDAP_DC2),
            ldap.SCOPE_SUBTREE,
            '(&(objectClass=user)(mail={}))'.format(email),
        )
        user_found = None
        for user_dn, entry in users_all:
            if 'mail' in entry:
                decoded_email = entry['mail'][0].decode('utf-8')
                if decoded_email == email:
                    user_found = (user_dn, entry)
        # _logger.info("found user by email: " + str(user_found))
        if not user_found:
            raise Exception('get_user_by_email error: User not found on AD: ' + email)
        return user_found

    def get_user_by_username(self, username: str) -> Tuple[str, dict]:
        '''
        Summary:
            get the user infomation in ldap by username

        Parameter:
            username(string): user name in ldap

        Return:
            user_dn(string): user dn in ldap
            user_info(dict): the rest infomation in user eg. group
        '''
        users = self.conn.search_s(
            'dc={},dc={}'.format(ConfigSettings.LDAP_DC1, ConfigSettings.LDAP_DC2),
            ldap.SCOPE_SUBTREE,
            f'(&(objectClass=user)(sAMAccountName={username}))',
        )

        user_found = None
        for user_dn, entry in users:
            if 'sAMAccountName' in entry:
                decoded_username = entry['sAMAccountName'][0].decode('utf-8')
                if decoded_username == username:
                    user_found = (user_dn, entry)

        if not user_found:
            _logger.info('user %s is not found in AD' % username)
            return None, None
        _logger.info('found user by username: ' + str(user_found))
        return user_found

    def is_account_in_ad(self, email: str) -> bool:
        try:
            self.get_user_by_email(email)
        except Exception:
            return False
        return True
