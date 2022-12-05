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

import requests
from common.services.logger_services.logger_factory_service import SrvLoggerFactory
# from flask import request
# from flask_restx import Resource

from fastapi import APIRouter
from fastapi_utils import cbv

from config import ConfigSettings
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
from models.accounts import AccountRequestPOST, ContractRequestPOST

from resources.error_handler import APIException
from resources.utils import fetch_geid
from resources.utils import get_formatted_datetime
from resources.error_handler import catch_internal

from services.data_providers.ldap_client import LdapClient
from services.data_providers.neo4j_client import Neo4jClient
from services.notifier_services.email_service import SrvEmail


router = APIRouter()

_API_TAG = '/v1/accounts'
_API_NAMESPACE = "accounts"

logger = SrvLoggerFactory(_API_NAMESPACE).get_logger()


# THE api is used directly from frontend to create test account
@cbv.cbv(router)
class AccountRequest:

    def add_user_to_ad_group(self, user_dn, group):
        try:
            ldap_client = LdapClient()
            ldap_client.connect(group)
            ldap_client.add_user_to_group(user_dn)
            ldap_client.disconnect()
        except Exception as e:
            error_msg = f"Error adding user to AD group: {str(e)}"
            logger.error(error_msg)
            raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=error_msg)

    def get_project_by_code(self, code):
        neo4j_client = Neo4jClient()
        response = neo4j_client.get_container_by_code(code)
        if response.get("code") != 200:
            error_msg = 'Error getting container in neo4j' + str(response.get("result"))
            logger.error(error_msg)
            raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=str(error_msg))
        return response["result"]

    def is_duplicate_user(self, username, email):
        neo4j_client = Neo4jClient()
        response = neo4j_client.node_query("User", {"username": username})
        if not response.get("result"):
            response = neo4j_client.node_query("User", {"email": email})

        if response.get("result"):
            user_node = response.get("result")[0]
            payload = {
                "start_label": "User",
                "end_label": "Container",
                "start_params": {
                    "email": user_node["email"]
                },
                "end_params": {
                    "code": ConfigSettings.TEST_PROJECT_CODE,
                }
            }
            response = requests.post(ConfigSettings.NEO4J_SERVICE + "relations/query", json=payload)
            if response.json():
                error_msg = f"User already exists in Neo4j in test project: {username}"
                logger.error(error_msg)
                raise APIException(
                    status_code=EAPIResponseCode.conflict.value,
                    error_msg=error_msg
                )
            else:
                # User exists but is not in test project
                notes = """
                This user is already exists and submitted a request for a Test Account from the Portal.
                Please contact the user to determine further action.
                """
                email_service = SrvEmail()
                email_service.send(
                    subject="Action Required: Existing user requested a Test Account",
                    receiver=ConfigSettings.EMAIL_SUPPORT,
                    sender=ConfigSettings.EMAIL_SUPPORT,
                    msg_type="html",
                    template="test_account/support_notification.html",
                    template_kwargs={
                        "title": "Test account request pending review",
                        "name": user_node.get("username"),
                        "first_name": user_node.get("first_name"),
                        "last_name": user_node.get("last_name"),
                        "email": email,
                        "project": ConfigSettings.TEST_PROJECT_CODE,
                        "status": "Pending Review",
                        "notes": notes,
                        'url': f'{ConfigSettings.DOMAIN_NAME}/{ConfigSettings.START_PATH}',
                    },
                )
                return True
            return False

    def create_user(self, email):
        neo4j_client = Neo4jClient()
        # Add neo4j user
        response = neo4j_client.create_user({
            "email": email,
            "role": "member",
            "status": "pending",
            "global_entity_id": fetch_geid(),
        })
        if response.get("code") != 200:
            error_msg = 'Error creating user in neo4j' + str(response.get("result"))
            logger.error(error_msg)
            raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=str(error_msg))
        user_node = response["result"]

        # Get project node
        project_node = self.get_project_by_code(ConfigSettings.TEST_PROJECT_CODE)

        # Add neo4j relation
        response = neo4j_client.create_relation(
            user_node["id"],
            project_node["id"],
            ConfigSettings.TEST_PROJECT_ROLE,
            properties={"status": "active"}
        )
        if response.get("code") != 200:
            error_msg = 'Error getting container in neo4j' + str(response.get("result"))
            logger.error(error_msg)
            raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=str(error_msg))


    @router.post("/accounts", tags=[_API_TAG],
                 summary='')
    @catch_internal(_API_NAMESPACE)
    async def post(self, data: AccountRequestPOST):
        res = APIResponse()
        # data = request.get_json()
        email = data.email
        username = data.username
        logger.info(f"TestRequest called: {username}")

        email_service = SrvEmail()
        neo4j_client = Neo4jClient()
        if self.is_duplicate_user(username, email):
            res.error_msg = f'duplicate user'
            res.code = EAPIResponseCode.bad_request
            return res.json_response()

        ldap_client = LdapClient()
        ldap_client.connect(ConfigSettings.TEST_PROJECT_CODE)
        user_dn, user_data = ldap_client.get_user_by_username(username)
        if not user_dn:
            # User not found, send alert to support
            logger.info(f"User not found in AD: {username}")
            email_service.send(
                subject="Request for a Test Account Denied - Invalid Username",
                receiver=ConfigSettings.EMAIL_SUPPORT,
                sender=ConfigSettings.EMAIL_SUPPORT,
                msg_type="html",
                template="test_account/support_notification.html",
                template_kwargs={
                    "title": "A test account request denied",
                    "username": username,
                    "email": email,
                    "project": ConfigSettings.TEST_PROJECT_CODE,
                    "status": "Denied",
                    "notes": "Username does not exist in Active Directory",
                    "send_date": get_formatted_datetime("CET"),
                    'url': f'{ConfigSettings.DOMAIN_NAME}/{ConfigSettings.START_PATH}',
                },
            )
            email_service.send(
                subject="Your request for a test account is under review",
                receiver=email,
                sender=ConfigSettings.EMAIL_SUPPORT,
                msg_type="html",
                template="test_account/review_notification.html",
                template_kwargs={
                    "first_name": username,
                    'url_guide': f'{ConfigSettings.DOMAIN_NAME}/{ConfigSettings.GUIDE_PATH}',
                    "support_email": ConfigSettings.EMAIL_SUPPORT,
                },
            )
            return res.json_response()

        ldap_email = user_data.get("mail")[0].decode()
        first_name = user_data.get("givenName", "")[0].decode()
        if not first_name:
            first_name = username
        last_name = user_data.get("sn", "")[0].decode()

        if ldap_email.lower() == email.lower():
            # User found in AD, create user and send email to user and support
            logger.info(f"User found in AD, email matches: {username}")
            self.add_user_to_ad_group(user_dn, ConfigSettings.LDAP_USER_GROUP)
            self.add_user_to_ad_group(user_dn, ConfigSettings.TEST_PROJECT_CODE)
            self.create_user(email)

            project_node = self.get_project_by_code(ConfigSettings.TEST_PROJECT_CODE)
            email_service.send(
                subject="Auto-Notification: Request for a Test Account Approved",
                receiver=ConfigSettings.EMAIL_SUPPORT,
                sender=ConfigSettings.EMAIL_SUPPORT,
                msg_type="html",
                template="test_account/support_notification.html",
                template_kwargs={
                    "first_name": first_name,
                    "last_name": last_name,
                    "username": username,
                    "email": email,
                    "project_name": ConfigSettings.TEST_PROJECT_CODE,
                    "title": "A test account request submitted and approved",
                    "status": "Approved",
                    "send_date": get_formatted_datetime("CET"),
                    'url': f'{ConfigSettings.DOMAIN_NAME}/{ConfigSettings.START_PATH}',
                },
            )
            email_service.send(
                subject="Your request for a test account has been approved",
                receiver=email,
                sender=ConfigSettings.EMAIL_SUPPORT,
                msg_type="html",
                template="test_account/user_created.html",
                template_kwargs={
                    "first_name": first_name,
                    "project_code": ConfigSettings.TEST_PROJECT_CODE,
                    "project_role": ConfigSettings.TEST_PROJECT_ROLE,
                    "project_name": project_node["name"],
                    'url': f'{ConfigSettings.DOMAIN_NAME}/{ConfigSettings.START_PATH}',
                    'url_guide': f'{ConfigSettings.DOMAIN_NAME}/{ConfigSettings.GUIDE_PATH}',
                    "support_email": ConfigSettings.EMAIL_SUPPORT,
                },
            )
        else:
            # User found in AD but email doesn't match, send email to support and notify user
            logger.info(f"User found in AD, email doesn't match: {username}")
            email_service.send(
                subject="Action Required: Request for a Test Account submitted, review required",
                receiver=ConfigSettings.EMAIL_SUPPORT,
                sender=ConfigSettings.EMAIL_SUPPORT,
                msg_type="html",
                template="test_account/support_notification.html",
                template_kwargs={
                    "title": "A test account request pending review",
                    "name": f"{first_name} {last_name}",
                    "username": username,
                    "email": email,
                    "project": ConfigSettings.TEST_PROJECT_CODE,
                    "status": "Pending Review",
                    "notes": "Email address does not match username in Active Directory",
                    "send_date": get_formatted_datetime("CET"),
                    'url': f'{ConfigSettings.DOMAIN_NAME}/{ConfigSettings.START_PATH}',
                },
            )
            email_service.send(
                subject="Your request for a test account is under review",
                receiver=email,
                sender=ConfigSettings.EMAIL_SUPPORT,
                msg_type="html",
                template="test_account/review_notification.html",
                template_kwargs={
                    "first_name": first_name,
                    'url_guide': f'{ConfigSettings.DOMAIN_NAME}/{ConfigSettings.GUIDE_PATH}',
                    "support_email": ConfigSettings.EMAIL_SUPPORT,
                },
            )
        ldap_client.disconnect()
        return res.json_response()

@cbv.cbv(router)
class ContractRequest:

    @router.post("/accounts/contract", tags=[_API_TAG],
                 summary='')
    @catch_internal(_API_NAMESPACE)
    async def post(self, data: ContractRequestPOST):
        res = APIResponse()
        # data = request.get_json()
        agreement_info = data.contract_description
        why_interested = data.interest_description
        email = data.email
        name = data.first_name + " " + data.last_name
        logger.info(f"ContractRequest called: {email}")

        email_service = SrvEmail()
        email_service.send(
            subject="Action Required: Pending Request for a Test Account",
            receiver=ConfigSettings.EMAIL_SUPPORT,
            sender=ConfigSettings.EMAIL_SUPPORT,
            msg_type="html",
            template="test_account/support_notification.html",
            template_kwargs={
                "title": "A test account request pending review",
                "name": name,
                "email": email,
                "project": ConfigSettings.TEST_PROJECT_CODE,
                "status": "Pending Review",
                "agreement_info": agreement_info,
                "why_interested": why_interested,
                "send_date": get_formatted_datetime("CET"),
                'url': f'{ConfigSettings.DOMAIN_NAME}/{ConfigSettings.START_PATH}',
            },
        )
        email_service.send(
            subject="Your request for a test account is under review",
            receiver=email,
            sender=ConfigSettings.EMAIL_SUPPORT,
            msg_type="html",
            template="test_account/contract_user_create.html",
            template_kwargs={
                'url_guide': f'{ConfigSettings.DOMAIN_NAME}/{ConfigSettings.GUIDE_PATH}',
                "support_email": ConfigSettings.EMAIL_SUPPORT,
            },
        )
        return res.json_response()
