from flask import request, after_this_request
from flask_restx import Api, Resource, fields
from module_keycloak.ops_admin import OperationsAdmin
from module_keycloak.ops_user import OperationsUser
from models.api_response import APIResponse, EAPIResponseCode
from keycloak import exceptions
from config import ConfigClass
from users import api
import requests
import json
import re


class UserAuth(Resource):
    # user login 
    ################################################################# Swagger
    payload = api.model(
        "query_payload_basic", {
            "username": fields.String(readOnly=True, description='username'),
            "password": fields.String(readOnly=True, description='password'),
            "realm": fields.String(readOnly=True, description='realm'),
        }
    )
    sample_return = '''
    {
        "code": 200,
        "error_msg": "",
        "result": {
            "access_token": "nbR6F90TUfZGsr0fL9rFVd77n-EZziIlnDdz3AFVF_XmQ",
            "expires_in": 300,
            "refresh_expires_in": 480,
            "refresh_token": "LbK6oDALEQuYCJA1STSFeTJy4",
            "token_type": "bearer",
            "not-before-policy": 0,
            "session_state": "9bf0981a-2825-4e5c-8d50-73aa7bc83586",
            "scope": "email profile"
        },
        "page": 1,
        "total": 1,
        "num_of_pages": 1
    }
    '''
    #################################################################
    @api.expect(payload)
    @api.response(200, sample_return)
    def post(self):
        try:
            res = APIResponse()
            post_data = request.get_json()
            username = post_data.get('username', None)
            password = post_data.get('password', None)  
            realm = post_data.get('realm', None) 
            print(username);print(password);print(realm)
            if not username or not password :
                res.set_result('Missing required information')
                res.set_code(EAPIResponseCode.bad_request)
                return res.response, res.code
            if not realm or not realm in ConfigClass.KEYCLOAK.keys():
                res.set_result('Invaild realm')
                res.set_code(EAPIResponseCode.bad_request)
                return res.response, res.code

            client_id = ConfigClass.KEYCLOAK[realm][0]
            client_secret = ConfigClass.KEYCLOAK[realm][1]
           
            # log in 
            user_client = OperationsUser(
                client_id,
                realm, 
                client_secret)
            token = user_client.get_token(username, password)
            res.set_result(token)
            res.set_code(EAPIResponseCode.success)
            return res.response, res.code
        except exceptions.KeycloakAuthenticationError as err:
            err_code = err.response_code
            error_msg = json.loads(err.response_body)
            return {"result": str(error_msg)}, err_code
        except exceptions.KeycloakGetError as err:
            print(err)
            err_code = err.response_code
            error_msg = json.loads(err.response_body)
            return {"result": str(error_msg)}, err_code
        except Exception as e:
            res.set_result(f'User authentication failed : {e}')
            res.set_code(EAPIResponseCode.internal_error)
            return res.response, res.code


class UserRefresh(Resource):
    # user refresh 
    ################################################################# Swagger
    payload = api.model(
        "user_refresh", {
            "realm":fields.String(readOnly=True, description='realm'),
            "refreshtoken": fields.String(readOnly=True, description='refreshtoken')
        }
    )
    sample_return = '''
    {
        "code": 200,
        "error_msg": "",
        "result": {
            "access_token": "eyJhbGcgIYYWkp9uBHKQRqw",
            "expires_in": 300,
            "refresh_expires_in": 480,
            "refresh_token": "OiJlbWFpbCBwcmZp6-xg4846zw4UJePZAzzAWI",
            "token_type": "bearer",
            "not-before-policy": 0,
            "session_state": "9bf0981a-2825-4e5c-8d50-73aa7bc83586",
            "scope": "email profile"
        },
        "page": 1,
        "total": 1,
        "num_of_pages": 1
    }
    '''
    #################################################################
    @api.expect(payload)
    @api.response(200, sample_return)
    def post(self):
        try:
            res = APIResponse()
            post_data = request.get_json()
            token = post_data.get('refreshtoken', None)
            realm = post_data.get('realm', None) 
            if not token:
                res.set_result('Missing refresh token')
                res.set_code(EAPIResponseCode.bad_request)
                return res.response, res.code
            if not realm or not realm in ConfigClass.KEYCLOAK.keys():
                res.set_result('Invaild realm')
                res.set_code(EAPIResponseCode.bad_request)
                return res.response, res.code

            client_id = ConfigClass.KEYCLOAK[realm][0]
            client_secret = ConfigClass.KEYCLOAK[realm][1]
            user_client = OperationsUser(
                client_id,
                realm, 
                client_secret)
            token = user_client.get_refresh_token(token)
            res.set_result(token)
            res.set_code(EAPIResponseCode.success)
            return res.response, res.code

        except exceptions.KeycloakGetError as err:
            err_code = err.response_code
            error_msg = json.loads(err.response_body)
            return {"result": str(error_msg)}, err_code
        except Exception as e:
            res.set_result(f'Unable to get token : {e}')
            res.set_code(EAPIResponseCode.internal_error)
            return res.response, res.code


class UserPassword(Resource):
    # user reset password
    ################################################################# Swagger
    payload = api.model(
        "user_password_payload", {
            "realm": fields.String(readOnly=True, description='realm'),
            "username": fields.String(readOnly=True, description='username'),
            "old_password": fields.String(readOnly=True, description='old password'),
            "new_password": fields.String(readOnly=True, description='new password'),
        }
    )
    sample_return = '''
    {
        "result": "success"
    }
    '''
    #################################################################
    @api.expect(payload)
    @api.response(200, sample_return)
    def put(self):
        # validate payload
        post_data = request.get_json()
        realm = post_data.get('realm', None)
        username = post_data.get('username', None)
        old_password = post_data.get('old_password', None)
        new_password = post_data.get('new_password', None)

        if realm is None or realm not in ConfigClass.KEYCLOAK.keys():
            return {'result': 'invalid realm'}, 400
        
        if username is None or old_password is None or new_password is None:
            return {'result': 'missing username, old password or new password'}, 400

        password_pattern = re.compile(ConfigClass.PASSWORD_REGEX)
        match = re.search(password_pattern, new_password)
        if not match:
            return {'result': 'invalid new password'}, 400

        # check old password
        client_id = ConfigClass.KEYCLOAK[realm][0]
        client_secret = ConfigClass.KEYCLOAK[realm][1]

        try:
            user_client = OperationsUser(
                    client_id,
                    realm, 
                    client_secret)
            res = user_client.get_token(username, old_password)
        except Exception as e:
            return {'result': 'incorrect realm, username or old password: {}'.format(e)}, 400

        # create admin client
        try:
            admin_client = OperationsAdmin(realm)
        except Exception as e:
            return {'result': 'invalid admin credentials: {}'.format(e)}, 500

        # get user id
        try:
            user_id = admin_client.get_user_id(username)
        except Exception as e:
            return {'result': 'cannot get user id: {}'.format(e)}, 500

        # set user password
        try:
            res = admin_client.set_user_password(user_id, new_password, False)
        except Exception as e:
            return {'result': 'cannot reset password: {}'.format(e)}, 500

        return {'result': 'success'}, 200

        

