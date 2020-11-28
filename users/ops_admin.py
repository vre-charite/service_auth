from config import ConfigClass
from module_keycloak.ops_admin import OperationsAdmin
from models.api_response import APIResponse, EAPIResponseCode
from keycloak import exceptions
from flask_restx import Api, Resource, fields
from flask import request
from flask_jwt import jwt_required
from datetime import datetime
from users import api 
import requests
import jwt
import json
import psycopg2

class CreateUser(Resource):
    # create user
    ##############################################################swagger
    payload = api.model(
        "create_user", {
            "realm": fields.String(readOnly=True, description='realm'),
            "username": fields.String(readOnly=True, description='username'),
            "password": fields.String(readOnly=True, description='password'),
            "email": fields.String(readOnly=True, description='email'),
            "firstname": fields.String(readOnly=True, description='firstname'),
            "lastname": fields.String(readOnly=True, description='lastname'),
        }
    )
    sample_return = '''
    {
        "code": 200,
        "error_msg": "",
        "result": "User created successfully",
        "page": 1,
        "total": 1,
        "num_of_pages": 1
    }
    '''
    #############################################################
    @api.expect(payload)
    @api.response(200, sample_return)
    def post(self):
        api.logger.info('Calling CreateAccount post')
        try:
            res = APIResponse()
            post_data = request.get_json()
            realm = post_data.get('realm', None)
            if not realm or not realm in ConfigClass.KEYCLOAK.keys():
                res.set_result('Invalid realm')
                res.set_code(EAPIResponseCode.bad_request)
                return res.response, res.code                     
            operations_admin = OperationsAdmin(realm)

            # get the request user data(to be created)
            username = post_data.get('username', None)
            password = post_data.get('password', None)
            email = post_data.get('email', None)
            firstname = post_data.get('firstname', None)
            lastname = post_data.get('lastname', None)
            if not username or not password or not email or not firstname or not lastname:
                res.set_result('Missing required information')
                res.set_code(EAPIResponseCode.bad_request)
                return res.response, res.code

            user = operations_admin.create_user(
                username, 
                password, 
                email, 
                firstname,
                lastname, 
                cred_type = "password",
                enabled = True)
                
            res.set_result('User created successfully')
            res.set_code(EAPIResponseCode.success)
            api.logger.info(f'CreateUser Successful for {username}')
            return res.response, res.code

        except exceptions.KeycloakGetError as err:
            err_code = err.response_code
            error_msg = json.loads(err.response_body)
            api.logger.error(str(error_msg))
            return {"result": str(error_msg)}, err_code
        except Exception as e:
            error_msg = f'User created failed: {e}'
            res.set_result(error_msg)
            res.set_code(EAPIResponseCode.internal_error)
            api.logger.error(error_msg)
            return res.response, res.code


class GetUserByUsername(Resource):
    ##############################################################swagger
    payload = api.model(
        "get_user_username", {
            "realm": fields.String(readOnly=True, description='realm'),
            "username": fields.String(readOnly=True, description='username'),
            "invite_code": fields.String(readOnly=True, description='invite_code'),
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
            ......
        },
        "page": 1,
        "total": 1,
        "num_of_pages": 1
    }
    '''
    #############################################################
    parser = api.parser()
    @api.expect(payload)
    @api.response(200, sample_return)
    def get(self):

        api.logger.info('Calling GetUserByUsername get')
        try:
            res = APIResponse()
            realm = request.args.get('realm', None)
            username = request.args.get('username', None)
            invite_code = request.args.get('invite_code', None)

            ops_db = psycopg2.connect(
                database=ConfigClass.RDS_DBNAME,
                user=ConfigClass.RDS_USER,
                password=ConfigClass.RDS_PWD,
                host=ConfigClass.RDS_HOST,
                port=ConfigClass.RDS_PORT,
            )
            cursor = ops_db.cursor()
            table = f"{ConfigClass.RDS_SCHEMA_DEFAULT}.user_invitation"

            query = f"SELECT * FROM {table} where invitation_code=%(invite_code)s ORDER BY create_timestamp asc"
            cursor.execute(query, { "invite_code": invite_code })
            result = cursor.fetchone();
            if not result:
                res.set_result('Invitation not valid')
                res.set_code(EAPIResponseCode.bad_request)
                return res.response, res.code

            expiry = result[2]
            if expiry <= datetime.now():
                res.set_result('Invitation expired')
                res.set_code(EAPIResponseCode.bad_request)
                return res.response, res.code

            if not username or not realm:
                res.set_result('Missing required information')
                res.set_code(EAPIResponseCode.bad_request)
                return res.response, res.code
            if not realm or realm not in ConfigClass.KEYCLOAK.keys():
                res.set_result('Invalid realm')
                res.set_code(EAPIResponseCode.bad_request)
                return res.response, res.code
            operations_admin = OperationsAdmin(realm)
            user_id = operations_admin.get_user_id(username)
            user = operations_admin.get_user_info( user_id)
            res.set_result(user)
            res.set_code(EAPIResponseCode.success)
            api.logger.info(f'GetUserByUsername Successful for {username}')
            return res.response, res.code
        except exceptions.KeycloakGetError as err:
            err_code = err.response_code
            error_msg = json.loads(err.response_body)
            api.logger.error(str(error_msg))
            return {"result": error_msg}, err_code
        except Exception as e:
            error_msg = f'query user by its name failed: {e}'
            res.set_result(error_msg)
            res.set_code(EAPIResponseCode.internal_error)
            api.logger.error(error_msg)
            return res.response, res.code
            
            
class GetUserByEmail(Resource):
    ##############################################################swagger
    payload = api.model(
        "get_user_email", {
            "realm": fields.String(readOnly=True, description='realm'),
            "email": fields.String(readOnly=True, description='email'),
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
    #############################################################
    parser = api.parser()
    @api.expect(payload)
    @api.response(200, sample_return)
    def get(self):
        api.logger.info('Calling GetUserByEmail get')
        try:
            res = APIResponse()

            email = request.args.get('email', None)
            realm = request.args.get('realm', None)

            if not email or not realm:
                res.set_result('Missing required information')
                res.set_code(EAPIResponseCode.bad_request)
                api.logger.info('Email or realm missing on request')
                return res.response, res.code
            if not realm or realm not in ConfigClass.KEYCLOAK.keys():
                res.set_result('Invalid realm')
                res.set_code(EAPIResponseCode.bad_request)
                return res.response, res.code

            operations_admin = OperationsAdmin(realm)
            user = operations_admin.get_user_by_email(email)
            if not user:
                res.set_result(None)
                res.set_code(EAPIResponseCode.not_found)
                api.logger.info(f'GetUserByEmail not found for {email}')
                return res.response, res.code
            user_info = operations_admin.get_user_info(user.get("id"))
            res.set_result(user_info)
            res.set_code(EAPIResponseCode.success)
            api.logger.info(f'GetUserByEmail Successful for {email}')
            return res.response, res.code
        except exceptions.KeycloakGetError as err:
            err_code = err.response_code
            error_msg = json.loads(err.response_body)
            api.logger.error(error_msg)
            return {"result": error_msg}, err_code
        except Exception as e:
            error_msg = f'query user by its email failed: {e}'
            res.set_result(error_msg)
            res.set_code(EAPIResponseCode.internal_error)
            api.logger.error(error_msg)
            return res.response, res.code


class UserGroup(Resource):

    ##############################################################swagger
    payload = api.model(
        "user_group", {
            "realm": fields.String(readOnly=True, description='realm'),
            "username": fields.String(readOnly=True, description='username'),
            "groupname": fields.String(readOnly=True, description='groupname'),
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
    #############################################################
    parser = api.parser()
    @api.expect(payload)
    @api.response(200, sample_return)
    def post(self):
        api.logger.info('Calling UserGroup post')
        try:
            res = APIResponse()
            data = request.get_json()
            realm = data.get("realm")
            username = data.get("username")
            groupname = data.get("groupname")
            if not username or not groupname or not realm: 
                res.set_result('Missing required information')
                res.set_code(EAPIResponseCode.bad_request)
                api.logger.info('Missing username, groupname or realm')
            operations_admin = OperationsAdmin(realm)
            user_id = operations_admin.get_user_id(username)
            group = operations_admin.keycloak_admin.get_group_by_path(f"/{groupname}")
            if not group:
                group_dict = {"name": groupname}
                operations_admin.keycloak_admin.create_group(group_dict)
                group = operations_admin.keycloak_admin.get_group_by_path(f"/{groupname}")
            operations_admin.keycloak_admin.group_user_add(user_id, group["id"])
            res.set_result('success')
            res.set_code(EAPIResponseCode.success)
            api.logger.info(f'UserGroup Successful for {username}')
            return res.response, res.code

        except Exception as e:
            error_msg = f'UserGroup failed' + str(e)
            res.set_result(error_msg)
            res.set_code(EAPIResponseCode.internal_error)
            api.logger.error(error_msg)
            return res.response, res.code

    @api.expect(payload)
    @api.response(200, sample_return)
    def delete(self):
        api.logger.info('Calling UserGroup delete')
        try:
            res = APIResponse()
            data = request.args
            realm = data.get("realm")
            username = data.get("username")
            groupname = data.get("groupname")
            if not username or not groupname or not realm: 
                res.set_result('Missing required information')
                res.set_code(EAPIResponseCode.bad_request)
                api.logger.info('Missing username, groupname or realm')
            operations_admin = OperationsAdmin(realm)
            user_id = operations_admin.get_user_id(username)
            group = operations_admin.keycloak_admin.get_group_by_path(f"/{groupname}")
            operations_admin.keycloak_admin.group_user_remove(user_id, group["id"])

            res.set_result('success')
            res.set_code(EAPIResponseCode.success)
            api.logger.info(f'UserGroup Successful for {username}')
            return res.response, res.code
        except Exception as e:
            error_msg = f'UserGroup delete failed' + str(e)
            res.set_result(error_msg)
            res.set_code(EAPIResponseCode.internal_error)
            api.logger.error(error_msg)
            return res.response, res.code


class UserManagement(Resource):
    ##############################################################swagger
    payload = api.model(
        "get_user_email", {
            "realm": fields.String(readOnly=True, description='realm'),
            "email": fields.String(readOnly=True, description='email'),
            "status": fields.String(readOnly=True, description='status'),
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
    #############################################################
    parser = api.parser()
    @api.expect(payload)
    @api.response(200, sample_return) 
    def put(self):
        api.logger.info('Calling GetUserByEmail get')
        try:
            res = APIResponse()

            payload = request.get_json()

            email = payload.get('email', None)
            realm = payload.get('realm', None)
            status = payload.get('status', None)

            if not email or not realm or not status:
                res.set_result('Missing required information')
                res.set_code(EAPIResponseCode.bad_request)
                api.logger.info('Email or realm missing on request')
                return res.response, res.code
            if not realm or realm not in ConfigClass.KEYCLOAK.keys():
                res.set_result('Invalid realm')
                res.set_code(EAPIResponseCode.bad_request)
                return res.response, res.code

            operations_admin = OperationsAdmin(realm)
            user = operations_admin.get_user_by_email(email)
            if not user:
                res.set_result(None)
                res.set_code(EAPIResponseCode.not_found)
                api.logger.info(f'GetUserByEmail not found for {email}')
                return res.response, res.code

            payload = {"enabled": False}
            if status == 'active':
                payload = {"enabled": True}

            operations_admin.update_user(user.get("id"), payload)
            user_info = operations_admin.get_user_info(user.get("id"))
            res.set_result(user_info)
            res.set_code(EAPIResponseCode.success)
            api.logger.info(f'GetUserByEmail Successful for {email}')
            return res.response, res.code
        except exceptions.KeycloakGetError as err:
            err_code = err.response_code
            error_msg = json.loads(err.response_body)
            api.logger.error(error_msg)
            return {"result": error_msg}, err_code
        except Exception as e:
            error_msg = f'query user by its email failed: {e}'
            res.set_result(error_msg)
            res.set_code(EAPIResponseCode.internal_error)
            api.logger.error(error_msg)
            return res.response, res.code
