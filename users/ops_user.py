from flask import request, after_this_request
from flask_restx import Api, Resource, fields
from module_keycloak.ops_admin import OperationsAdmin
from module_keycloak.ops_user import OperationsUser
from models.api_response import APIResponse, EAPIResponseCode
from keycloak import exceptions
from config import ConfigClass
from users import api
from datetime import datetime
import requests
import json
import re


class UserAuth(Resource):
    # user login 
    ################################################################ Swagger
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
    ################################################################
    @api.expect(payload)
    @api.response(200, sample_return)
    def post(self):
        api.logger.info('Calling UserAuth post')
        try:
            res = APIResponse()
            post_data = request.get_json()
            username = post_data.get('username', None)
            password = post_data.get('password', None)  
            realm = ConfigClass.KEYCLOAK_REALM

            if not username or not password :
                res.set_result('Missing required information')
                res.set_code(EAPIResponseCode.bad_request)
                api.logger.info('Username or Password missing on request')
                return res.response, res.code
            if not realm or realm not in ConfigClass.KEYCLOAK.keys():
                res.set_result('Invalid realm')
                res.set_code(EAPIResponseCode.bad_request)
                api.logger.info(f'Invalid realm: {realm}')
                return res.response, res.code

            client_id = ConfigClass.KEYCLOAK[realm][0]
            client_secret = ConfigClass.KEYCLOAK[realm][1]
           
            # log in 
            user_client = OperationsUser(
                client_id,
                realm, 
                client_secret)
            token = user_client.get_token(username, password)
            user_info = user_client.get_userinfo()

            if user_info['preferred_username'] != username:
                error_msg = 'User authentication failed '
                res.set_result(error_msg)
                res.set_code(EAPIResponseCode.unauthorized)
                api.logger.error(error_msg)
                return res.response, res.code

            # Get neo4j user id by username
            try:
                response = requests.post(
                    ConfigClass.NEO4J_SERVICE + "nodes/User/query", 
                    json={"name": username}
                )
                neo4j_user_id = json.loads(response.content)[0]["id"]
                last_login = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")
                response = requests.put(
                    ConfigClass.NEO4J_SERVICE + f"nodes/User/node/{neo4j_user_id}", 
                    json={"last_login": str(last_login)}
                )
            except Exception as e:
                api.logger.error("Error updating last_login " + str(e))

            res.set_result(token)
            res.set_code(EAPIResponseCode.success)
            api.logger.info(f'UserAuth Successful for {username} on realm {realm}')
            return res.response, res.code
        except exceptions.KeycloakAuthenticationError as err:
            err_code = err.response_code
            error_msg = json.loads(err.response_body)
            api.logger.error(error_msg)
            return {"result": error_msg}, err_code
        except exceptions.KeycloakGetError as err:
            err_code = err.response_code
            error_msg = json.loads(err.response_body)
            api.logger.error(str(error_msg))
            return {"result": error_msg}, err_code
        except Exception as e:
            error_msg = f'User authentication failed : {e}'
            res.set_result(error_msg)
            res.set_code(EAPIResponseCode.internal_error)
            api.logger.error(error_msg)
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
        api.logger.info('Calling UserRefresh post')
        try:
            res = APIResponse()
            post_data = request.get_json() or {}
            token = post_data.get('refreshtoken', None)
            realm = ConfigClass.KEYCLOAK_REALM
            if not token:
                error_msg = 'Missing refresh token'
                res.set_result(error_msg)
                res.set_code(EAPIResponseCode.bad_request)
                api.logger.info(error_msg)
                return res.response, res.code
            if not realm or realm not in ConfigClass.KEYCLOAK.keys():
                res.set_result('Invalid realm')
                res.set_code(EAPIResponseCode.bad_request)
                api.logger.info(f'Invalid realm: {realm}')
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
            api.logger.info('UserRefresh Successful')
            return res.response, res.code

        except exceptions.KeycloakGetError as err:
            err_code = err.response_code
            error_msg = json.loads(err.response_body)
            api.logger.error(error_msg)
            return {"result": error_msg}, err_code
        except Exception as e:
            error_msg = f'Unable to get token : {e}'
            res.set_result(error_msg)
            res.set_code(EAPIResponseCode.internal_error)
            api.logger.error(error_msg)
            return res.response, res.code

class UserLastLogin(Resource):
    payload = api.model(
        "query_payload_basic", {
            "username": fields.String(readOnly=True, description='username'),
        }
    )
    sample_return = {"result": "success"}

    @api.expect(payload)
    @api.response(200, sample_return)
    def post(self):
        username = request.get_json().get("username")

        if not username:
            return {"result": "Missing username"}, 400

        response = requests.post(
            ConfigClass.NEO4J_SERVICE + "nodes/User/query", 
            json={"name": username}
        )
        neo4j_user_id = json.loads(response.content)[0]["id"]
        last_login = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")
        response = requests.put(
            ConfigClass.NEO4J_SERVICE + f"nodes/User/node/{neo4j_user_id}", 
            json={"last_login": str(last_login)}
        )
        return {"result": "success"}, 200


class UserStatus(Resource):
    def get(self):
        email = request.args.get("email")
        if not email:
            return {"result": "Missing email"}, 400
        response = requests.post(
            ConfigClass.NEO4J_SERVICE + "nodes/User/query", 
            json={"email": email}
        )
        if response.status_code != 200:
            return response
        if not response.json():
            return {"result": "User not found"}, 404
        user_node = response.json()[0]
        result = {
            "email": email,
            "status": user_node["status"],
        }
        return result, 200

class UserProjectRole(Resource):
    def post(self):
        post_data = request.get_json()
        print(post_data)
        realm = ConfigClass.KEYCLOAK_REALM
        email = post_data.get("email", None)
        project_role = post_data.get("project_role", None)
        if not realm or not email or not project_role:
            return {"error_message": "email/realm required"}, 400
        # create admin client
        try:
            admin_client = OperationsAdmin(realm)
        except Exception as e:
            error_msg = f'invalid admin credentials: {e}'
            api.logger.error(error_msg)
            return {'result': error_msg }, 500
        user = admin_client.get_user_by_email(email)
        assign_result = admin_client.assign_user_role(user['id'], project_role)
        return {"result": 'success'}, 200

    def delete(self):
        post_data = request.get_json()
        realm = ConfigClass.KEYCLOAK_REALM
        email = post_data.get("email", None)
        project_role = post_data.get("project_role", None)
        if not realm or not email or not project_role:
            return {"error_message": "email/realm required"}, 400
        # create admin client
        try:
            admin_client = OperationsAdmin(realm)
        except Exception as e:
            error_msg = f'invalid admin credentials: {e}'
            api.logger.error(error_msg)
            return {'result': error_msg }, 500
        user = admin_client.get_user_by_email(email)
        response = admin_client.delete_role_of_user(user['id'], project_role)
        if not response.status_code  in [200, 204]:
            return response.json(), response.status_code
        return {"result": 'success'}, 200
