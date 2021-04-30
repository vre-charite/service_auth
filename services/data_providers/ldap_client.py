import ldap
from config import ConfigClass
from services.logger_services.logger_factory_service import SrvLoggerFactory

_logger = SrvLoggerFactory('ldap client').get_logger()

class LdapClient():
    '''
    Ldap client
    '''

    def __init__(self):
        pass

    def connect(self, dn_code):
        '''
        need build connection before using ldap client
        '''
        self.conn = ldap.initialize(ConfigClass.LDAP_URL)
        self.dn = "cn=vre-{},ou=Gruppen,ou={},dc={},dc={}".format(
            dn_code, ConfigClass.LDAP_OU, ConfigClass.LDAP_DC1, ConfigClass.LDAP_DC2)
        self.objectclass = []
        self.objectclass.append(ConfigClass.LDAP_objectclass.encode('utf-8'))
        self.conn.simple_bind_s(ConfigClass.LDAP_ADMIN_DN,
                                ConfigClass.LDAP_ADMIN_SECRET)

    def disconnect(self):
        self.conn.unbind_s()

    def add_user_to_group(self, user_dn):
        operation_list = []
        operation_list.append((ldap.MOD_ADD, 'member', [user_dn.encode('utf-8')]))
        res = self.conn.modify_s(
            self.dn,
            operation_list
        )
        return res

    def remove_user_from_group(self, user_dn):
        _logger.info("removed user: " + user_dn)
        _logger.info("remove user from group dn: " + self.dn)
        operation_list = []
        operation_list.append(
            (ldap.MOD_DELETE, 'member', [user_dn.encode('utf-8')]))

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
        _logger.info("search users dn: " + "dc={},dc={}".format(ConfigClass.LDAP_DC1, ConfigClass.LDAP_DC2))
        users = self.conn.search_s(
            "dc={},dc={}".format(
                ConfigClass.LDAP_DC1, ConfigClass.LDAP_DC2),
            ldap.SCOPE_SUBTREE,
            '(objectClass=user)'
        )
        _logger.info("number of users found: " + str(len(users)))
        return users

    def get_user_by_email(self, email):
        '''
        return tuple(user_dn, entry)
        '''
        users_all = self.get_all_users()
        user_found = None
        for user_dn, entry in users_all:
            if 'mail' in entry:
                decoded_email = entry['mail'][0].decode("utf-8")
                if decoded_email == email:
                    user_found = (user_dn, entry)
        _logger.info("found user by email: " + str(user_found))
        return user_found

    def get_user_by_username(self, username):
        '''
        Return ldap user dn by given cn
        '''
        users = self.conn.search_s(
            "dc={},dc={}".format(
                ConfigClass.LDAP_DC1, ConfigClass.LDAP_DC2),
            ldap.SCOPE_SUBTREE,
            u"(cn={})".format(username)
        )
        return users
