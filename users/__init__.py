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

from common.services.logger_services.logger_factory_service import SrvLoggerFactory
from flask_restx import Api

from resources.error_handler import APIException

# from flask_restful import Api
module_api = Api(
    version='1.0',
    title='User management API',
    description='User API',
    doc='/v1/api-doc',
)

api = module_api.namespace('user_management', description='Operation on users', path='/')
api.logger.addHandler(SrvLoggerFactory('auth').get_logger())


@module_api.errorhandler(APIException)
def http_exception_handler(exc: APIException):
    return exc.content, exc.status_code


# user operations
# from users.ops_user import UserAuth, UserRefresh, UserLastLogin, UserStatus, UserProjectRole
# api.add_resource(UserAuth, '/v1/users/auth')
# api.add_resource(UserRefresh, '/v1/users/refresh')
# api.add_resource(UserLastLogin, '/v1/users/lastlogin')
# api.add_resource(UserStatus, '/v1/user/status')
# api.add_resource(UserProjectRole, '/v1/user/project-role')

# admin-only operations
# from users.ops_admin import CreateUser, GetUserByUsername, GetUserByEmail, UserGroup, UserGroupAll, SyncGroupTrigger, RealmRoles, UserProjectRoleAll
# api.add_resource(GetUserByUsername, '/v1/users/name')
# api.add_resource(CreateUser, '/v1/admin/users')
# api.add_resource(GetUserByEmail, '/v1/admin/users/email')
# api.add_resource(UserGroup, '/v1/admin/users/group')
# api.add_resource(SyncGroupTrigger, '/v1/admin/users/group/sync')
# api.add_resource(RealmRoles, '/v1/admin/users/realm-roles')
# api.add_resource(UserGroupAll, '/v1/admin/users/group/all')
# api.add_resource(UserProjectRoleAll, '/v1/admin/users/project-role/all')

# from users.user_account_management import UserADGroupOperations, UserManagementV1
# api.add_resource(UserManagementV1, '/v1/user/account')
# api.add_resource(UserADGroupOperations, '/v1/user/ad-group')

# from users.permissions.permissions import Authorize
# api.add_resource(Authorize, '/v1/authorize')

# from users.accounts import AccountRequest, ContractRequest
# api.add_resource(AccountRequest, '/v1/accounts')
# api.add_resource(ContractRequest, '/v1/accounts/contract')
