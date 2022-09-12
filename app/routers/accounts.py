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

import httpx
import requests
from common.services.logger_services.logger_factory_service import SrvLoggerFactory
from fastapi import APIRouter
from fastapi_utils import cbv

from app.config import ConfigSettings
from app.models.accounts import AccountRequestPOST, ContractRequestPOST
from app.models.api_response import APIResponse, EAPIResponseCode
from app.resources.error_handler import APIException, catch_internal
from app.resources.keycloak_api.ops_admin import OperationsAdmin
from app.resources.utils import get_formatted_datetime
from app.services.data_providers.ldap_client import LdapClient
from app.services.notifier_services.email_service import SrvEmail

# from flask import request
# from flask_restx import Resource


router = APIRouter()

_API_TAG = '/v1/accounts'
_API_NAMESPACE = 'accounts'

logger = SrvLoggerFactory(_API_NAMESPACE).get_logger()


# THE api is used directly from frontend to create test account
@cbv.cbv(router)
class AccountRequest:
    def is_duplicate_user(self, username: str, email: str) -> bool:

        # get user all roles
        admin_client = OperationsAdmin(ConfigSettings.KEYCLOAK_REALM)
        user_info = admin_client.get_user_by_email(email)
        # if user not exist then return false to proceed the user
        # account request flow
        if not user_info:
            return False

        # now will mapping the test project role to see if user
        # has any of them if no send the email. if yes raise the
        # duplicate error
        realm_roles = admin_client.get_user_realm_roles(user_info.get('id'))
        test_project_role = [
            ConfigSettings.TEST_PROJECT_CODE + '-admin',
            ConfigSettings.TEST_PROJECT_CODE + '-collaborator',
            ConfigSettings.TEST_PROJECT_CODE + '-contributor',
        ]

        if [x for x in realm_roles if x in test_project_role]:
            error_msg = f'User: {username} already exists in the test project'
            logger.error(error_msg)
            raise APIException(status_code=EAPIResponseCode.conflict.value, error_msg=error_msg)
        else:
            # User exists but is not in test project
            notes = """
            This user is already exists and submitted a request for a Test Account from the Portal.
            Please contact the user to determine further action.
            """
            email_service = SrvEmail()
            email_service.send(
                subject='Action Required: Existing user requested a Test Account',
                receiver=ConfigSettings.EMAIL_SUPPORT,
                sender=ConfigSettings.EMAIL_SUPPORT,
                msg_type='html',
                template='test_account/support_notification.html',
                template_kwargs={
                    'title': 'Test account request pending review',
                    'name': user_info.get('username'),
                    'first_name': user_info.get('firsName'),
                    'last_name': user_info.get('lastName'),
                    'email': email,
                    'project': ConfigSettings.TEST_PROJECT_CODE,
                    'status': 'Pending Review',
                    'notes': notes,
                    'url': f'{ConfigSettings.DOMAIN_NAME}/{ConfigSettings.START_PATH}',
                },
            )
            return True

        return False

    @router.post('/accounts', tags=[_API_TAG], summary='')
    @catch_internal(_API_NAMESPACE)
    async def post(self, data: AccountRequestPOST):
        '''
        Summary:
            The api is, for those who interest in platform and want
            to have a try, to adding them into the test project. here
            are some condition:
                - User should be not in the target project
                - User should exist in the AD
            otherwise the api will send email to admin to ask adding
            new user into platform

        Payload(AccountRequestPOST):
            - username(string): the unique username in keycloak
            - email(string): the target user email

        Return:
            200 success

        '''

        res = APIResponse()
        email = data.email
        username = data.username
        logger.info(f'TestRequest called: {username}')

        email_service = SrvEmail()
        if self.is_duplicate_user(username, email):
            res.error_msg = f'duplicate user'
            res.code = EAPIResponseCode.bad_request
            return res.json_response()

        ldap_client = LdapClient()
        user_dn, user_data = ldap_client.get_user_by_username(username)

        # User not found, send alert to support
        if not user_dn:
            logger.info(f'User not found in AD: {username}')
            email_service.send(
                subject='Request for a Test Account Denied - Invalid Username',
                receiver=ConfigSettings.EMAIL_SUPPORT,
                sender=ConfigSettings.EMAIL_SUPPORT,
                msg_type='html',
                template='test_account/support_notification.html',
                template_kwargs={
                    'title': 'A test account request denied',
                    'username': username,
                    'email': email,
                    'project': ConfigSettings.TEST_PROJECT_CODE,
                    'status': 'Denied',
                    'notes': 'Username does not exist in Active Directory',
                    'send_date': get_formatted_datetime('CET'),
                    'url': f'{ConfigSettings.DOMAIN_NAME}/{ConfigSettings.START_PATH}',
                },
            )
            email_service.send(
                subject='Your request for a test account is under review',
                receiver=email,
                sender=ConfigSettings.EMAIL_SUPPORT,
                msg_type='html',
                template='test_account/review_notification.html',
                template_kwargs={
                    'first_name': username,
                    'url_guide': f'{ConfigSettings.DOMAIN_NAME}/{ConfigSettings.GUIDE_PATH}',
                    'support_email': ConfigSettings.EMAIL_SUPPORT,
                },
            )
            res.result = 'Request for a test account is under review'
            return res.json_response()

        ldap_email = user_data.get('mail')[0].decode()
        first_name = user_data.get('givenName', '')[0].decode()
        if not first_name:
            first_name = username
        last_name = user_data.get('sn', '')[0].decode()

        if ldap_email.lower() == email.lower():
            # User found in AD, create user and send email to user and support
            logger.info(f'User found in AD, email matches: {username}')

            try:
                ldap_user_group = ldap_client.format_group_dn(ConfigSettings.LDAP_USER_GROUP)
                ldap_client.add_user_to_group(user_dn, ldap_user_group)
                project_group = ldap_client.format_group_dn(ConfigSettings.TEST_PROJECT_CODE)
                ldap_client.add_user_to_group(user_dn, project_group)
            except Exception as e:
                error_msg = f'Error adding user to AD group: {str(e)}'
                logger.error(error_msg)
                ldap_client.disconnect()
                raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=error_msg)

            email_service.send(
                subject='Auto-Notification: Request for a Test Account Approved',
                receiver=ConfigSettings.EMAIL_SUPPORT,
                sender=ConfigSettings.EMAIL_SUPPORT,
                msg_type='html',
                template='test_account/support_notification.html',
                template_kwargs={
                    'first_name': first_name,
                    'last_name': last_name,
                    'username': username,
                    'email': email,
                    'project_name': ConfigSettings.TEST_PROJECT_CODE,
                    'title': 'A test account request submitted and approved',
                    'status': 'Approved',
                    'send_date': get_formatted_datetime('CET'),
                    'url': f'{ConfigSettings.DOMAIN_NAME}/{ConfigSettings.START_PATH}',
                },
            )
            email_service.send(
                subject='Your request for a test account has been approved',
                receiver=email,
                sender=ConfigSettings.EMAIL_SUPPORT,
                msg_type='html',
                template='test_account/user_created.html',
                template_kwargs={
                    'first_name': first_name,
                    'project_code': ConfigSettings.TEST_PROJECT_CODE,
                    'project_role': ConfigSettings.TEST_PROJECT_ROLE,
                    'project_name': ConfigSettings.TEST_PROJECT_NAME,
                    'url': f'{ConfigSettings.DOMAIN_NAME}/{ConfigSettings.START_PATH}',
                    'url_guide': f'{ConfigSettings.DOMAIN_NAME}/{ConfigSettings.GUIDE_PATH}',
                    'support_email': ConfigSettings.EMAIL_SUPPORT,
                },
            )
            res.result = 'Request for a test account has been approved'
        else:
            # User found in AD but email doesn't match, send email to support and notify user
            logger.info(f"User found in AD, email doesn't match: {username}")
            email_service.send(
                subject='Action Required: Request for a Test Account submitted, review required',
                receiver=ConfigSettings.EMAIL_SUPPORT,
                sender=ConfigSettings.EMAIL_SUPPORT,
                msg_type='html',
                template='test_account/support_notification.html',
                template_kwargs={
                    'title': 'A test account request pending review',
                    'name': f'{first_name} {last_name}',
                    'username': username,
                    'email': email,
                    'project': ConfigSettings.TEST_PROJECT_CODE,
                    'status': 'Pending Review',
                    'notes': 'Email address does not match username in Active Directory',
                    'send_date': get_formatted_datetime('CET'),
                    'url': f'{ConfigSettings.DOMAIN_NAME}/{ConfigSettings.START_PATH}',
                },
            )
            email_service.send(
                subject='Your request for a test account is under review',
                receiver=email,
                sender=ConfigSettings.EMAIL_SUPPORT,
                msg_type='html',
                template='test_account/review_notification.html',
                template_kwargs={
                    'first_name': first_name,
                    'url_guide': f'{ConfigSettings.DOMAIN_NAME}/{ConfigSettings.GUIDE_PATH}',
                    'support_email': ConfigSettings.EMAIL_SUPPORT,
                },
            )
            res.result = 'Request for a test account is under review'
        ldap_client.disconnect()
        return res.json_response()


@cbv.cbv(router)
class ContractRequest:
    @router.post('/accounts/contract', tags=[_API_TAG], summary='')
    @catch_internal(_API_NAMESPACE)
    async def post(self, data: ContractRequestPOST):
        '''
        Summary:
            The api is used to based on the client to send a email
            to request the contract user

        Payload(ContractRequestPOST):
            - agreement_info(string): description field
            - why_interested(string): description field
            - email(string): user email
            - first_name(string): user first name
            - last_name(string): user first name

        Return:
            200 success

        '''

        res = APIResponse()

        agreement_info = data.contract_description
        why_interested = data.interest_description
        email = data.email
        name = data.first_name + ' ' + data.last_name
        logger.info(f'ContractRequest called: {email}')

        email_service = SrvEmail()
        email_service.send(
            subject='Action Required: Pending Request for a Test Account',
            receiver=ConfigSettings.EMAIL_SUPPORT,
            sender=ConfigSettings.EMAIL_SUPPORT,
            msg_type='html',
            template='test_account/support_notification.html',
            template_kwargs={
                'title': 'A test account request pending review',
                'name': name,
                'email': email,
                'project': ConfigSettings.TEST_PROJECT_CODE,
                'status': 'Pending Review',
                'agreement_info': agreement_info,
                'why_interested': why_interested,
                'send_date': get_formatted_datetime('CET'),
                'url': f'{ConfigSettings.DOMAIN_NAME}/{ConfigSettings.START_PATH}',
            },
        )
        email_service.send(
            subject='Your request for a test account is under review',
            receiver=email,
            sender=ConfigSettings.EMAIL_SUPPORT,
            msg_type='html',
            template='test_account/contract_user_create.html',
            template_kwargs={
                'url_guide': f'{ConfigSettings.DOMAIN_NAME}/{ConfigSettings.GUIDE_PATH}',
                'support_email': ConfigSettings.EMAIL_SUPPORT,
            },
        )
        return res.json_response()
