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
import httpx
from fastapi import APIRouter
from fastapi_utils import cbv
# from flask import request
# from flask_restx import fields
# from flask_restx import Resource
from keycloak import exceptions

from resources.error_handler import catch_internal

from config import ConfigSettings
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
from models.ops_admin import UserGroupPOST, RealmRolesPOST, \
    UserInRolePOST

from module_keycloak.ops_admin import OperationsAdmin
# from users import api


router = APIRouter()

_API_TAG = '/v1/admin'
_API_NAMESPACE = "api_admin_ops"

# logger = SrvLoggerFactory(_API_NAMESPACE).get_logger()



# this api is to check if user exist
@cbv.cbv(router)
class GetUserByEmail:
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
    # parser = api.parser()

    @router.get("/admin/users/email", tags=[_API_TAG],
                 summary='admin operateion get user by given email')
    @catch_internal(_API_NAMESPACE)
    async def get(self, email: str):
        # api.logger.info('Calling GetUserByEmail get')
        try:
            res = APIResponse()

            # email = request.args.get('email', None)
            realm = ConfigSettings.KEYCLOAK_REALM

            operations_admin = OperationsAdmin(realm)
            user = operations_admin.get_user_by_email(email)
            if not user:
                res.error_msg = "Cannot find user"
                res.code = EAPIResponseCode.not_found
                # api.logger.info(f'GetUserByEmail not found for {email}')
                return res.json_response()

            user_info = operations_admin.get_user_info(user.get("id"))
            res.result = user_info
            res.code = EAPIResponseCode.success
            # api.logger.info(f'GetUserByEmail Successful for {email}')
            
        except exceptions.KeycloakGetError as err:
            res.error_msg = json.loads(err.response_body)
            res.code = EAPIResponseCode.bad_request

        except Exception as e:
            res.error_msg = f'query user by its email failed: {e}'
            res.code = EAPIResponseCode.internal_error

        return res.json_response()



# this api is used when create project
@cbv.cbv(router)
class UserGroup:
    
    @router.post("/admin/users/group", tags=[_API_TAG],
                 summary='add user to existing group')
    @catch_internal(_API_NAMESPACE)
    async def post(self, data: UserGroupPOST):
        # api.logger.info('Calling UserGroup post')
        res = APIResponse()
        try:
            # data = request.get_json()
            realm = ConfigSettings.KEYCLOAK_REALM
            username = data.username
            groupname = data.groupname

            operations_admin = OperationsAdmin(realm)
            user_id = operations_admin.get_user_id(username)
            group = operations_admin.keycloak_admin.get_group_by_path(f"/{groupname}")
            if not group:
                group_dict = {"name": groupname}
                operations_admin.keycloak_admin.create_group(group_dict)
                group = operations_admin.keycloak_admin.get_group_by_path(f"/{groupname}")

            operations_admin.keycloak_admin.group_user_add(user_id, group["id"])
            res.result = 'success'
            res.code = EAPIResponseCode.success
        except Exception as e:
            # error_msg = f'UserGroup failed' + str(e)
            res.error_msg = f'UserGroup failed' + str(e)
            res.code = EAPIResponseCode.internal_error

        return res.json_response()


    @router.delete("/admin/users/group", tags=[_API_TAG],
                 summary='add user to existing group')
    @catch_internal(_API_NAMESPACE)
    async def delete(self, username: str, groupname: str):
        # api.logger.info('Calling UserGroup delete')
        res = APIResponse()
        try:
            realm = ConfigSettings.KEYCLOAK_REALM

            operations_admin = OperationsAdmin(realm)
            user_id = operations_admin.get_user_id(username)
            group = operations_admin.keycloak_admin.get_group_by_path(f"/{groupname}")
            operations_admin.keycloak_admin.group_user_remove(user_id, group["id"])
            
            res.result = 'success'
            res.code = EAPIResponseCode.success
            # api.logger.info(f'UserGroup Successful for {username}')
            # return res.response, res.code
        except Exception as e:
            # error_msg = f'UserGroup delete failed' + str(e)
            res.error_msg = f'UserGroup delete failed' + str(e)
            res.code = EAPIResponseCode.internal_error
            # api.logger.error(error_msg)
            # return res.response, res.code

        return res.json_response()


# this api is used in project creation to create three new role in keycloak
@cbv.cbv(router)
class RealmRoles:

    @router.post("/admin/users/realm-roles", tags=[_API_TAG],
                 summary='add new realm roles in keycloak')
    @catch_internal(_API_NAMESPACE)
    async def post(self, data: RealmRolesPOST):
        # api.logger.info('Create Project Realm Roles API')

        res = APIResponse()
        try:
            # payload = request.get_json()
            project_roles = data.project_roles
            project_code = data.project_code

            operations_admin = OperationsAdmin(ConfigSettings.KEYCLOAK_REALM)
            keycloak_res = operations_admin.create_project_realm_roles(project_roles, project_code)

            if keycloak_res != 'created':
                res.error_msg = keycloak_res
                res.code = EAPIResponseCode.internal_error
                return res.json_response()

            res.result = keycloak_res
            res.code = EAPIResponseCode.success
            # return res.response, res.code
        except Exception as e:
            # error_msg = f'create realm roles in keycloak failed: {e}'
            res.error_msg = f'create realm roles in keycloak failed: {e}'
            res.code = EAPIResponseCode.internal_error
            # api.logger.error(error_msg)
            # return res.response, res.code

        return res.json_response()


@cbv.cbv(router)
class UserInRole:

    @router.post("/admin/roles/users", tags=[_API_TAG],
                 summary='')
    @catch_internal(_API_NAMESPACE)
    async def post(self, data: UserInRolePOST):

        # The native api does not support any seaching/join/sorting/pagination, 
        # so I temporary do them manually
        # ALL the in memory sorting, searching, mapping are the temporary solution
        # at the end, they will be sync to some primary db

        res = APIResponse()
        order_by = data.order_by
        order_type = data.order_type
        page = data.page
        page_size = data.page_size
        username = data.username
        email = data.email
        status = data.status

        total_users = 0

        # intialize the keycloak admin to get token
        admin_client = OperationsAdmin(ConfigSettings.KEYCLOAK_REALM)
        hearder = {
            "Authorization": "Bearer "+admin_client.token.get("access_token"),
            "Content-Type": "application/json"
        }

        user_list = []
        with httpx.Client() as client:
            for role in data.role_names:
                api = ConfigSettings.KEYCLOAK_SERVER_URL+"admin/realms/"+ConfigSettings.KEYCLOAK_REALM+"/roles/"+role+"/users"
                api_res = client.get(api, headers=hearder)

                # then return only certain of attributes to frontend
                user_list += [{
                    "username":user.get("username"),
                    "first_name":user.get("firstName"),
                    "last_name":user.get("lastName"),
                    "email":user.get("email"),
                    "permission": role.split("-")[-1]
                } for user in api_res.json()]

        # the keycloak native api doesnot support the searching
        # manually to do the searching since the users is about 10
        if username:
            user_list = [user for user in user_list if username in user.get("username")]
        if email:
            user_list = [user for user in user_list if email in user.get("email")]
        if status:
            user_list = [user for user in user_list if status == user.get("attributes",{}).get("status")]
        

        # here since the keycloak is NOT supporting sorting
        # manually sort the user by order_by and order_type
        if order_by:
            user_list = sorted(user_list, key=lambda user: user.get(order_by), reverse=True if order_type == 'desc' else False)

        # manually do the pagination
        total_users = len(user_list)
        user_list = user_list[page*page_size:(page+1)*page_size]

        res.result = user_list
        res.total = total_users
        res.num_of_pages = math.ceil(total_users / page_size)
        res.page = page

        return res.json_response()