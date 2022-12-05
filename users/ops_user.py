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

import json
import math
from datetime import datetime
from platform import platform
import requests
import httpx

from fastapi import APIRouter
from fastapi_utils import cbv
from keycloak import exceptions

from config import ConfigSettings
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
from module_keycloak.ops_admin import OperationsAdmin
from module_keycloak.ops_user import OperationsUser

from resources.error_handler import catch_internal

from models.ops_user import UserAuthPOST, UserTokenRefreshPOST, \
    UserLastLoginPOST, UserProjectRolePOST, UserProjectRoleDELETE


# from users import api

router = APIRouter()

_API_TAG = 'v1/auth'
_API_NAMESPACE = "api_auth"


# might be used by skd
@cbv.cbv(router)
class UserAuth:

    def __init__(self):
        # self.__logger = SrvLoggerFactory('api_data_download').get_logger()

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
    @router.post("/users/auth", tags=[_API_TAG],
                 summary='make the user authentication and return the access token')
    @catch_internal(_API_NAMESPACE)
    async def post(self, data: UserAuthPOST):
        # api.logger.info('Calling UserAuth post')
        res = APIResponse()
        try:
            username = data.username
            password = data.password

            realm = ConfigSettings.KEYCLOAK_REALM
            client_id = ConfigSettings.KEYCLOAK_CLIENT_ID
            client_secret = ConfigSettings.KEYCLOAK_SECRET

            # log in
            user_client = OperationsUser(client_id, realm, client_secret)
            token = user_client.get_token(username, password)
            user_info = user_client.get_userinfo()

            if user_info['preferred_username'] != username:
                # error_msg = 'User authentication failed '
                res.error_msg = 'User authentication failed.'
                res.code = EAPIResponseCode.unauthorized
                # api.logger.error(error_msg)
                return res.json_response()

            # Get neo4j user id by username
            try:
                response = requests.post(
                    ConfigSettings.NEO4J_SERVICE + "nodes/User/query",
                    json={"name": username}
                )
                neo4j_user_id = json.loads(response.content)[0]["id"]
                last_login = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")
                response = requests.put(
                    ConfigSettings.NEO4J_SERVICE + f"nodes/User/node/{neo4j_user_id}",
                    json={"last_login": str(last_login)}
                )
            except Exception as e:
                # api.logger.error("Error updating last_login " + str(e))
                pass

            res.result = token
            res.code = EAPIResponseCode.success
            # api.logger.info(f'UserAuth Successful for {username} on realm {realm}')
            # return res.response, res.code
        except exceptions.KeycloakAuthenticationError as err:
            res.error_msg = str(err)
            res.code = EAPIResponseCode.unauthorized
        except exceptions.KeycloakGetError as err:
            res.error_msg = str(err)
            res.code = EAPIResponseCode.unauthorized
        except Exception as e:
            res.error_msg = f'User authentication failed : {e}'
            res.code = EAPIResponseCode.internal_error
            # api.logger.error(error_msg)

        return res.json_response()


# might be used by skd
@cbv.cbv(router)
class UserRefresh:

    def __init__(self):
        # self.__logger = SrvLoggerFactory('api_data_download').get_logger()
        # user refresh

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
    @router.post("/users/refresh", tags=[_API_TAG],
                summary='refresh the user token and issue a new one')
    @catch_internal(_API_NAMESPACE)
    async def post(self, data: UserTokenRefreshPOST):
        # api.logger.info('Calling UserRefresh post')
        res = APIResponse()
        try:
            token = data.refreshtoken

            realm = ConfigSettings.KEYCLOAK_REALM
            client_id = ConfigSettings.KEYCLOAK_CLIENT_ID
            client_secret = ConfigSettings.KEYCLOAK_SECRET
            user_client = OperationsUser(client_id, realm, client_secret)
            token = user_client.get_refresh_token(token)

            res.result = token
            res.code = EAPIResponseCode.success
            # api.logger.info('UserRefresh Successful')

        except exceptions.KeycloakGetError as err:
            res.error_msg = str(err)
            res.code = EAPIResponseCode.internal_error

        except Exception as e:
            error_msg = f'Unable to get token : {e}'
            res.error_msg = f'Unable to get token : {e}'
            res.code = EAPIResponseCode.internal_error

        return res.json_response()


# This api is used by portal to update user last login
@cbv.cbv(router)
class UserLastLogin:

    def __init__(self):
        # self.__logger = SrvLoggerFactory('api_data_download').get_logger()
        # payload = api.model(
        #     "query_payload_basic", {
        #         "username": fields.String(readOnly=True, description='username'),
        #     }
        # )
        sample_return = {"result": "success"}

    @router.post("/users/lastlogin", tags=[_API_TAG],
                summary='save the user last login time')
    @catch_internal(_API_NAMESPACE)
    async def post(self, data: UserLastLoginPOST):

        res = APIResponse()
        username = data.username

        # if not username:
        #     return {"result": "Missing username"}, 400
        try:
            # get user by username to fetch the id
            response = requests.post(
                ConfigSettings.NEO4J_SERVICE + "nodes/User/query",
                json={"name": username}
            )
            users = response.json()
            if len(users) == 0:
                res.error_msg = "User not exists"
                res.code = EAPIResponseCode.bad_request
                return res.json_response()

            neo4j_user_id = users[0]["id"]

            # add last login time
            last_login = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")
            response = requests.put(
                ConfigSettings.NEO4J_SERVICE + f"nodes/User/node/{neo4j_user_id}",
                json={"last_login": str(last_login)}
            )

            res.result = response.json()
            res.code = EAPIResponseCode.success

        except Exception as e:
            res.error_msg = str(e)
            res.code = EAPIResponseCode.internal_error

        return res.json_response()


# This api is used by portal to check if user is activate
@cbv.cbv(router)
class UserStatus:

    def __init__(self):
        pass

    @router.get("/user/status", tags=[_API_TAG],
                summary='save the user last login time')
    @catch_internal(_API_NAMESPACE)
    async def get(self, email: str):
        # email = request.args.get("email")
        res = APIResponse()
        
        try:
            # query the user from neo4j
            response = requests.post(
                ConfigSettings.NEO4J_SERVICE + "nodes/User/query",
                json={"email": email}
            )
            if response.status_code != 200:
                res.error_msg = response.json()
                res.code = EAPIResponseCode.bad_request
                return res.json_response()
            # if not response.json():
            #     return {"result": "User not found"}, 404

            user_node = response.json()[0]
            res.result = {
                "email": email,
                "status": user_node["status"],
            }
            res.code = EAPIResponseCode.success
        except Exception as e:
            res.error_msg = "User not exists"
            res.code = EAPIResponseCode.not_found

        return res.json_response()


# this api is used by portal to add user into projects
@cbv.cbv(router)
class UserProjectRole:

    def __init__(self):
        pass
    
    @router.post("/user/project-role", tags=[_API_TAG],
                summary='list the project role for given user')
    @catch_internal(_API_NAMESPACE)
    async def post(self, data: UserProjectRolePOST):
        
        res = APIResponse()
        realm = ConfigSettings.KEYCLOAK_REALM
        email = data.email
        project_role = data.project_role

        # create admin client
        try:
            admin_client = OperationsAdmin(realm)
            user = admin_client.get_user_by_email(email)
            admin_client.assign_user_role(user['id'], project_role)

            res.result = "success"
            res.code = EAPIResponseCode.success

        except Exception as e:
            res.error_msg = f'invalid admin credentials: {e}'
            res.code = EAPIResponseCode.internal_error
    
        return res.json_response()


    @router.delete("/user/project-role", tags=[_API_TAG],
                summary='remove the project role for given user')
    @catch_internal(_API_NAMESPACE)
    async def delete(self, data: UserProjectRoleDELETE):
        
        res = APIResponse()
        realm = ConfigSettings.KEYCLOAK_REALM
        email = data.email
        project_role = data.project_role
        
        # create admin client
        try:
            admin_client = OperationsAdmin(realm)
            user = admin_client.get_user_by_email(email)
            admin_client.delete_role_of_user(user['id'], project_role)

            res.result = "success"
            res.code = EAPIResponseCode.success

        except Exception as e:
            res.error_msg = f'invalid admin credentials: {e}'
            res.code = EAPIResponseCode.success

        return res.json_response()


# new api to list user from keycloak
@cbv.cbv(router)
class UserList:

    def __init__(self):
        pass
    
    @router.get("/users", tags=[_API_TAG],
                summary='list users from keycloak')
    @catch_internal(_API_NAMESPACE)
    async def get(self, username:str=None, email:str=None, page:int=0, page_size:int=10,
        exact:str="False", status:str=None, order_by:str=None, order_type:str="asc"):
        res = APIResponse()

        # for now the api does not support the exact search and status check
        # This will need to be wait until keycloak is upto v16
        # The native api does not support join/sorting, so I temporary do them manually
        # ALL the in memory sorting, searching, mapping are the temporary solution
        # at the end, they will be sync to some primary db

        # create admin client
        admin_client = OperationsAdmin(ConfigSettings.KEYCLOAK_REALM)
        hearder = {
            "Authorization": "Bearer "+admin_client.token.get("access_token"),
            "Content-Type": "application/json"
        }
        query = {
            "username":username,
            "email": email, 
            "first": page,
            "max": page_size,
            # "exact": 'true'
        }
        
        # NOTE HERE: the keycloak api does not support sorting
        # consider the amount of the user ~100. so I decide to use
        # python to do the sorting
        if order_by:
            query.update({
                "first": 0,
                "max": 1000,
            })

        # get the total user count
        api = ConfigSettings.KEYCLOAK_SERVER_URL+"admin/realms/"+ConfigSettings.KEYCLOAK_REALM+"/users/count"
        with httpx.Client() as client:
            api_res = client.get(api, headers=hearder, params=query)
        total_users = api_res.json()

        # get user detail
        api = ConfigSettings.KEYCLOAK_SERVER_URL+"admin/realms/"+ConfigSettings.KEYCLOAK_REALM+"/users"
        with httpx.Client() as client:
            api_res = client.get(api, headers=hearder, params=query)
        users = api_res.json()
        

        # here since the keycloak is NOT supporting sorting
        # manually sort the user by order_by and order_type
        if order_by:

            # generate order lambda the special one is last_login_time
            # this is attached to attribute so we have to get one more step
            order_lambda = lambda user: user.get(order_by)
            if order_by == "last_login":
                order_lambda = lambda user: user.get("attributes").get("last_login")

            users = sorted(users, key=order_lambda, reverse=True if order_type == 'desc' else False)
            # manually do the pagination
            users = users[page*page_size:(page+1)*page_size]

        for x in users:
            print(x)

        # finally filter out only return certain attributes
        users = [{
            "username":user.get("username"),
            "first_name":user.get("firstName"),
            "last_name":user.get("lastName"),
            "email":user.get("email"),
            "time_created": datetime.fromtimestamp(user.get("createdTimestamp")//1000).strftime("%Y-%m-%dT%H:%M:%S"),
            "last_login": user.get("attributes", {}).get("last_login"),
            "status": user.get("attributes", {}).get("status", 'active'),
        } for user in api_res.json()]


        # also manually do the platform admin check
        with httpx.Client() as client:
            api = ConfigSettings.KEYCLOAK_SERVER_URL+"admin/realms/"+ConfigSettings.KEYCLOAK_REALM+"/roles/platform-admin/users"
            api_res = client.get(api, headers=hearder)
            platform_admins = [x.get("username") for x in api_res.json()]
        # then do the looping over to match the return with platform admin
        # since the page is 10 and platform admin is ~10
        for user in users:
            if user.get("username") in platform_admins or user.get("username") == "admin":
                user.update({"role":"admin"})
            else:
                user.update({"role":"member"})


        res.result = users
        res.total = total_users
        res.num_of_pages = math.ceil(total_users / page_size)
        res.page = page

        return res.json_response()