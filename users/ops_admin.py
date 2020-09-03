from config import ConfigClass
from module_keycloak.ops_admin import OperationsAdmin
from models.api_response import APIResponse, EAPIResponseCode
from keycloak import exceptions
from flask_restx import Api, Resource, fields
from flask import request
from flask_jwt import jwt_required
from users import api 
import requests
import jwt
import json

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
        try:
            res = APIResponse()
            post_data = request.get_json()
            realm = post_data.get('realm', None)
            if not realm or not realm in ConfigClass.KEYCLOAK.keys():
                res.set_result('Invaild realm')
                res.set_code(EAPIResponseCode.bad_request)
                return res.response, res.code                     
            operations_admin = OperationsAdmin(realm)

            # get the request user data(to be created)
            username = post_data.get('username', None)
            password = post_data.get('password', None)
            email = post_data.get('email', None)
            firstname = post_data.get('firstname', None)
            lastname = post_data.get('lastname', None)
            print("username");print(username);   print("password");print(password)                                         # for debug
            print("email");print(email);         print("firstname");print(firstname);   print("lastname");print(lastname)  # for debug
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
            print("created user is : "+user)
            return res.response, res.code

        except exceptions.KeycloakGetError as err:
            err_code = err.response_code
            error_msg = json.loads(err.response_body)
            return {"result": str(error_msg)}, err_code
        except Exception as e:
            res.set_result(f'User created failed : {e}')
            res.set_code(EAPIResponseCode.internal_error)
            return res.response, res.code


class GetUserByUsername(Resource):
    ##############################################################swagger
    payload = api.model(
        "get_user_username", {
            "realm": fields.String(readOnly=True, description='realm'),
            "username": fields.String(readOnly=True, description='username'),
        }
    )
    sample_return = '''
    {
        "code": 200,
        "error_msg": "",
        "result": "{
            'id': '9229f648-cfad-4851-8a3c-4b46b9d94d08',
            'createdTimestamp': 1598365933269, 
            'username': 'samantha', 
            'enabled': True,
            ......
        }",
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
        try:
            res = APIResponse()
            realm = request.args.get('realm', None)
            print(realm)
            username = request.args.get('username', None)
            print("username");print(realm)  # for debug
            if not username or not realm:
                res.set_result('Missing required information')
                res.set_code(EAPIResponseCode.bad_request)
                return res.response, res.code
            if not realm or not realm in ConfigClass.KEYCLOAK.keys():
                res.set_result('Invaild realm')
                res.set_code(EAPIResponseCode.bad_request)
                return res.response, res.code
            operations_admin = OperationsAdmin(realm)
            user_id = operations_admin.get_user_id(username)
            user = operations_admin.get_user_info( user_id)
            print(user)
            res.set_result(str(user))
            res.set_code(EAPIResponseCode.success)
            return res.response, res.code
        except exceptions.KeycloakGetError as err:
                err_code = err.response_code
                error_msg = json.loads(err.response_body)
                return {"result": str(error_msg)}, err_code
        except Exception as e:
            res.set_result(f'query user by its name failed: {e}')
            res.set_code(EAPIResponseCode.internal_error)
            return res.response, res.code
            
            
class GetUserByEmail(Resource):
    ##############################################################swagger
    payload = api.model(
        "get_user_email", {
            "container_id": fields.Integer(readOnly=True, description='container id'),
            "email": fields.String(readOnly=True, description='email'),
        }
    )
    sample_return = '''
    {
        "result": "User harry1 already in the project please check."
    }
    '''
    #############################################################
    parser = api.parser()
    @api.expect(payload)
    @api.response(200, sample_return)
    def get(self):

        email = request.args.get('email', None)
        container_id = request.args.get('container_id', None)
        print(container_id)

        # neo4j is the source of truth
        # first we try to get the user from neo4js
        # Check if user is existed
        url = ConfigClass.NEO4J_SERVICE + "nodes/User/query"
        res = requests.post(
            url=url,
            json={"email": email}
        )
        users = json.loads(res.text)
        if(len(users) == 0):
            return {'result': "email %s does not exist in platform." % email}, 404
        user_id = users[0]['id']
        username  = users[0]['name']

        # also check if they alreay have the relationsihp
        url = ConfigClass.NEO4J_SERVICE + "relations/query"
        res = requests.post(
            url=url,
            json={
                'start_label': 'User', 
                'start_params':{'id':user_id},
                'end_label': 'Dataset', 
                'end_params':{'id':int(container_id)},
            }
        )
        if res.status_code != 200:
            return {'result': res.text}, res.status_code 

        user_dataset_relation = res.json()
        print(user_dataset_relation)
        if len(user_dataset_relation) > 0:
            return {'result': 'User %s already in the project please check.' % username}, 403

        return {'result': username}, 200

