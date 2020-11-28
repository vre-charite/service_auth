from flask_restx import Api, Resource, fields
from services.logger_services.logger_factory_service import SrvLoggerFactory

# from flask_restful import Api
module_api = Api(
    version='1.0', 
    title='User management API',
    description='User API', 
    doc='/v1/api-doc'
)

# api = Api()
api = module_api.namespace('user_management', description='Operation on users', path ='/')
api.logger.addHandler(SrvLoggerFactory("auth").get_logger())


# user operations
from users.ops_user import UserAuth, UserRefresh, UserPassword
api.add_resource(UserAuth, '/v1/users/auth')
api.add_resource(UserRefresh, '/v1/users/refresh')
api.add_resource(UserPassword, '/v1/users/password')

# admin-only operations 

from users.ops_admin import CreateUser, GetUserByUsername, GetUserByEmail, UserGroup, UserManagement
api.add_resource(GetUserByUsername, '/v1/users/name')
api.add_resource(CreateUser, '/v1/admin/users')
api.add_resource(GetUserByEmail,'/v1/admin/users/email')
api.add_resource(UserGroup, '/v1/admin/users/group')
api.add_resource(UserManagement, '/v1/admin/users/management')

# password reset endpoints
from users.ops_reset import SendResetEmail, ChangePassword, CheckToken, SendUsername
api.add_resource(SendResetEmail, '/v1/users/reset/send-email')
api.add_resource(CheckToken, '/v1/users/reset/check-token')
api.add_resource(ChangePassword, '/v1/users/reset/password')
api.add_resource(SendUsername, '/v1/users/reset/send-username')
