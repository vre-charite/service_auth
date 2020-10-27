from flask_restx import Resource, fields
from flask import request, render_template
from datetime import datetime, timedelta
import uuid
import re
from keycloak import exceptions

from module_keycloak.ops_admin import OperationsAdmin
from models.api_response import APIResponse, EAPIResponseCode
from services.notifier_services.email_service import SrvEmail
from config import ConfigClass
from users import api
from resources.utils import sql_query, mask_email


class SendResetEmail(Resource):
    # user login 
    ################################################################# Swagger
    payload = api.model(
        "send_reset_email", {
            "username": fields.String(readOnly=True, description='email'),
            "realm": fields.String(readOnly=True, description='realm'),
        }
    )
    sample_return = '''
    {
        "code": 200,
        "error_msg": "",
        "result": "g**g@****.**",
        "page": 1,
        "total": 1,
        "num_of_pages": 1
    }
    '''
    #################################################################
    @api.expect(payload)
    @api.response(200, sample_return)
    def post(self):
        api.logger.info('Calling SendResetEmail post')
        try:
            res = APIResponse()
            post_data = request.get_json()
            username = post_data.get('username', None)
            realm = post_data.get('realm', None)
            if not username or not realm or realm not in ConfigClass.KEYCLOAK.keys():
                res.set_result('Missing required information')
                res.set_code(EAPIResponseCode.bad_request)
                api.logger.info('email or realm missing on request')
                return res.response, res.code

            operations_admin = OperationsAdmin(realm)
            try:
                user_id = operations_admin.get_user_id(username)
                keycloak_data = operations_admin.get_user_info(user_id)
            except exceptions.KeycloakGetError as err:
                res.set_result('User not found')
                res.set_code(EAPIResponseCode.not_found)
                api.logger.info(f'user not found with username {username}')
                return res.response, res.code 

            if not keycloak_data:
                res.set_result('User not found')
                res.set_code(EAPIResponseCode.not_found)
                api.logger.info(f'user not found with email {keycloak_data["email"]}')
                return res.response, res.code

            reset_token = uuid.uuid4().hex

            table = f"{ConfigClass.RDS_SCHEMA_DEFAULT}.user_password_reset"
            query = f"INSERT INTO {table} (reset_token, email, expiry_timestamp) values \
                    (%(reset_token)s, %(email)s, %(expiry_timestamp)s) RETURNING *"
            expiry = datetime.now() + timedelta(hours=ConfigClass.PASSWORD_RESET_EXPIRE_HOURS)
            expiry = expiry.isoformat()
            sql_params = {
                "reset_token": reset_token,
                "email": keycloak_data["email"],
                "expiry_timestamp": expiry
            }
            sql_query(query, sql_params)
            reset_link = ConfigClass.PASSWORD_RESET_URL_PREFIX + f"account-assistant/reset-password?token={reset_token}"

            # Get email HTML from template
            html_msg = render_template(
                "reset_password.html",
                username=keycloak_data["username"],
                reset_link=reset_link,
                admin_email=ConfigClass.EMAIL_ADMIN_CONNECTION,
                hours=ConfigClass.PASSWORD_RESET_EXPIRE_HOURS
            )
            # Send reset email
            subject = "VRE password reset"
            email_sender = SrvEmail()
            email_result = email_sender.send(
                subject,
                html_msg,
                [keycloak_data["email"]],
                msg_type="html",
            )
            email = mask_email(keycloak_data["email"])

            res.set_result(email)
            res.set_code(EAPIResponseCode.success)
            api.logger.info('SendResetEmail Successful')
            return res.response, res.code
        except Exception as e:
            error_msg = f'SendResetEmail failed : {e}'
            res.set_result(error_msg)
            res.set_code(EAPIResponseCode.internal_error)
            api.logger.error(error_msg)
            return res.response, res.code


class CheckToken(Resource):
    # user login 
    ################################################################# Swagger
    payload = api.model(
        "check_token", {
            "token": fields.String(readOnly=True, description='token'),
            "realm": fields.String(readOnly=True, description='realm'),
        }
    )
    sample_return = '''
    {
        "code": 200,
        "error_msg": "",
        "result": {
            'id': '9229f648-cfad-4851-8a3c-4b46b9d94d08',
            'createdTimestamp': 1598365933269,
            'username': 'samantha',
            'enabled': True,
            'email': 'test@test.com',
            ......
        },
        "page": 1,
        "total": 1,
        "num_of_pages": 1
    }
    '''
    #################################################################

    @api.expect(payload)
    @api.response(200, sample_return)
    def get(self):
        api.logger.info('Calling CheckToken get')
        try:
            res = APIResponse()
            token = request.args.get('token', None)
            realm = request.args.get('realm', None)

            table = f"{ConfigClass.RDS_SCHEMA_DEFAULT}.user_password_reset"
            query = f"SELECT * FROM {table} where reset_token=%(reset_token)s ORDER BY expiry_timestamp asc"
            result = sql_query(query, {"reset_token": token}, fetch=True)
            if not result:
                res.set_result('Token not valid')
                res.set_code(EAPIResponseCode.bad_request)
                return res.response, res.code

            expiry = result[2]
            if expiry <= datetime.now():
                res.set_result('Token expired')
                res.set_code(EAPIResponseCode.bad_request)
                return res.response, res.code

            operations_admin = OperationsAdmin(realm)
            keycloak_data = operations_admin.get_user_by_email(result[1])

            res.set_result(keycloak_data)
            res.set_code(EAPIResponseCode.success)
            api.logger.info('SendResetEmail Successful')
            return res.response, res.code
        except Exception as e:
            error_msg = f'CheckToken failed : {e}'
            res.set_result(error_msg)
            res.set_code(EAPIResponseCode.internal_error)
            api.logger.error(error_msg)
            return res.response, res.code


class ChangePassword(Resource):
    # user login 
    ################################################################# Swagger
    payload = api.model(
        "change_password", {
            "token": fields.String(readOnly=True, description='token'),
            "password": fields.String(readOnly=True, description='password'),
            "realm": fields.String(readOnly=True, description='realm'),
        }
    )
    sample_return = '''
    {
        "code": 200,
        "error_msg": "",
        "result": "success",
        "page": 1,
        "total": 1,
        "num_of_pages": 1
    }
    '''
    #################################################################

    @api.expect(payload)
    @api.response(200, sample_return)
    def post(self):
        api.logger.info('Calling ChangePassword post')
        try:
            res = APIResponse()
            post_data = request.get_json()
            token = post_data.get('token', None)
            password = post_data.get('password', None)
            realm = post_data.get('realm', None)
            if not password or not realm or realm not in ConfigClass.KEYCLOAK.keys():
                res.set_result('Missing required information')
                res.set_code(EAPIResponseCode.bad_request)
                api.logger.info('email or realm missing on request')
                return res.response, res.code

            table = f"{ConfigClass.RDS_SCHEMA_DEFAULT}.user_password_reset"
            query = f"SELECT * FROM {table} where reset_token=%(reset_token)s ORDER BY expiry_timestamp asc"
            result = sql_query(query, {"reset_token": token}, fetch=True)

            if not result:
                res.set_result('Token not valid')
                res.set_code(EAPIResponseCode.forbidden)
                return res.response, res.code

            expiry = result[2]
            if expiry <= datetime.now():
                res.set_result('Token expired')
                res.set_code(EAPIResponseCode.forbidden)
                return res.response, res.code

            password_pattern = re.compile(ConfigClass.PASSWORD_REGEX)
            match = re.search(password_pattern, password)
            if not match:
                error_msg = 'invalid new password'
                api.logger.info(error_msg)
                return {'result': error_msg}, 406

            operations_admin = OperationsAdmin(realm)
            keycloak_data = operations_admin.get_user_by_email(result[1])
            operations_admin.set_user_password(keycloak_data['id'], password, False)

            query = f"UPDATE {table} set expiry_timestamp=%(expiry)s where reset_token=%(reset_token)s"
            sql_params = {
                "expiry": datetime.now(),
                "reset_token": token,
            }
            sql_query(query, sql_params)

            res.set_result("success")
            res.set_code(EAPIResponseCode.success)
            return res.response, res.code
        except Exception as e:
            error_msg = f'ChangePassword failed : {e}'
            res.set_result(error_msg)
            res.set_code(EAPIResponseCode.internal_error)
            api.logger.error(error_msg)
            return res.response, res.code


class SendUsername(Resource):
    ################################################################# Swagger
    payload = api.model(
        "send_username", {
            "email": fields.String(readOnly=True, description='token'),
            "realm": fields.String(readOnly=True, description='realm'),
        }
    )
    sample_return = '''
    {
        "code": 200,
        "error_msg": "",
        "result": "success",
        "page": 1,
        "total": 1,
        "num_of_pages": 1
    }
    '''
    #################################################################

    @api.expect(payload)
    @api.response(200, sample_return)
    def post(self):
        api.logger.info('Calling SendUsername post')
        try:
            res = APIResponse()
            post_data = request.get_json()
            email = post_data.get('email', None)
            realm = post_data.get('realm', None)
            if not email or not realm or realm not in ConfigClass.KEYCLOAK.keys():
                res.set_result('Missing required information')
                res.set_code(EAPIResponseCode.bad_request)
                api.logger.info('email or realm missing on request')
                return res.response, res.code

            operations_admin = OperationsAdmin(realm)
            try:
                keycloak_data = operations_admin.get_user_by_email(email)
            except exceptions.KeycloakGetError as err:
                res.set_result('User not found')
                res.set_code(EAPIResponseCode.not_found)
                api.logger.info(f'user not found with email {email}')
                return res.response, res.code 

            if not keycloak_data:
                res.set_result('User not found')
                res.set_code(EAPIResponseCode.not_found)
                api.logger.info(f'user not found with email {email}')
                return res.response, res.code


            # Get email HTML from template
            html_msg = render_template(
                "reset_username.html",
                username=keycloak_data["username"],
                admin_email=ConfigClass.EMAIL_ADMIN_CONNECTION
            )
            # Send reset email
            subject = "VRE username"
            email_sender = SrvEmail()
            email_result = email_sender.send(
                subject,
                html_msg,
                [keycloak_data["email"]],
                msg_type="html",
            )
            res.set_result("success")
            res.set_code(EAPIResponseCode.success)
            api.logger.info('SendUsername Successful')
            return res.response, res.code
        except Exception as e:
            error_msg = f'SendUsername failed : {e}'
            res.set_result(error_msg)
            res.set_code(EAPIResponseCode.internal_error)
            api.logger.error(error_msg)
            return res.response, res.code
