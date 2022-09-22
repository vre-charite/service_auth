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

import math

from fastapi import APIRouter
from fastapi_sqlalchemy import db
from fastapi_utils.cbv import cbv
from logger import LoggerFactory

from app.commons.project_services import get_project_by_geid
from app.commons.psql_services.invitation import create_invite, query_invites
from app.config import ConfigSettings
from app.models.api_response import APIResponse, EAPIResponseCode
from app.models.invitation import (
    InvitationListPOST,
    InvitationPOST,
    InvitationPOSTResponse,
    InvitationPUT,
)
from app.models.sql_invitation import InvitationModel
from app.resources.error_handler import APIException
from app.resources.keycloak_api.ops_admin import OperationsAdmin
from app.routers.invitation.invitation_notify import send_emails
from app.services.data_providers.ldap_client import LdapClient

router = APIRouter()

_API_TAG = 'Invitation'


@cbv(router)
class Invitation:
    _logger = LoggerFactory('api_invitation').get_logger()

    @router.post(
        '/invitations',
        response_model=InvitationPOSTResponse,
        summary='Creates an new invitation',
        tags=[_API_TAG]
    )
    def create_invitation(self, data: InvitationPOST):
        self._logger.info('Called create_invitation')
        res = APIResponse()
        email = data.email
        platform_role = data.platform_role
        relation_data = data.relationship
        project_role = relation_data.get('project_role')

        project = None
        if relation_data:
            project = get_project_by_geid(relation_data.get('project_geid'))
            query = {'project_id': project['global_entity_id'], 'email': email}
            if query_invites(query):
                res.result = 'Invitation for this user already exists'
                res.code = EAPIResponseCode.conflict
                return res.json_response()

        admin_client = OperationsAdmin(ConfigSettings.KEYCLOAK_REALM)
        if admin_client.get_user_by_email(email):
            self._logger.info('User already exists in platform')
            res.result = '[ERROR] User already exists in platform'
            res.code = EAPIResponseCode.bad_request
            return res.json_response()

        account_in_ad = False
        if ConfigSettings.ENABLE_ACTIVE_DIRECTORY:
            ldap_cli = LdapClient()
            account_in_ad = ldap_cli.is_account_in_ad(email)
            if account_in_ad:
                group_dn = ldap_cli.format_group_dn(ConfigSettings.AD_USER_GROUP)
                user_dn, _ = ldap_cli.get_user_by_email(email)
                ldap_cli.add_user_to_group(user_dn, group_dn)
                if platform_role == 'admin':
                    group_dn = ldap_cli.format_group_dn(ConfigSettings.AD_ADMIN_GROUP)
                    ldap_cli.add_user_to_group(user_dn, group_dn)
                elif relation_data:
                    group_dn = ldap_cli.format_group_dn(project['code'])
                    ldap_cli.add_user_to_group(user_dn, group_dn)

        model_data = {
            'email': email,
            'invited_by': data.invited_by,
            'project_role': project_role,
            'platform_role': platform_role,
            'status': 'pending',
        }
        if project:
            model_data['project_id'] = project['global_entity_id']
        invitation_entry = create_invite(model_data)
        send_emails(invitation_entry, project, account_in_ad)
        res.result = 'success'
        return res.json_response()

    @router.get(
        '/invitation/check/{email}',
        response_model=InvitationPOSTResponse,
        summary="This method allow to get user's detail on the platform.",
        tags=[_API_TAG]
    )
    def check_user(self, email: str, project_geid: str = ''):
        self._logger.info('Called check_user')
        res = APIResponse()
        admin_client = OperationsAdmin(ConfigSettings.KEYCLOAK_REALM)
        user_info = admin_client.get_user_by_email(email)
        project = None
        if not user_info:
            invite = db.session.query(InvitationModel).filter_by(email=email, status="pending").first()
            if invite:
                res.result = {
                    'name': '',
                    'email': invite.email,
                    'status': 'invited',
                    'role': invite.platform_role,
                    'relationship': {},
                }
                return res.json_response()
            raise APIException(status_code=EAPIResponseCode.not_found.value, error_msg='User not found in keycloak')
        if project_geid:
            project = get_project_by_geid(project_geid)

        roles = admin_client.get_user_realm_roles(user_info['id'])
        platform_role = 'member'
        project_role = ''
        for role in roles:
            if 'platform-admin' == role['name']:
                platform_role = 'admin'
            if project and project['code'] == role['name'].split('-')[0]:
                project_role = role['name'].split('-')[1]
        res.result = {
            'name': user_info['username'],
            'email': user_info['email'],
            'status': user_info['attributes'].get('status', ['pending'])[0],
            'role': platform_role,
            'relationship': {},
        }
        if project and project_role:
            res.result['relationship'] = {
                'project_code': project['code'],
                'project_role': project_role,
                'project_geid': project['global_entity_id'],
            }
        return res.json_response()

    @router.post(
        '/invitation-list',
        response_model=InvitationPOSTResponse,
        summary='list invitations from psql',
        tags=[_API_TAG]
    )
    def invitation_list(self, data: InvitationListPOST):
        self._logger.info('Called invitation_list')
        res = APIResponse()
        query = {}
        for field in ['project_id', 'status']:
            if data.filters.get(field):
                query[field] = data.filters[field]
        try:
            invites = db.session.query(InvitationModel).filter_by(**query)
            for field in ['email', 'invited_by']:
                if data.filters.get(field):
                    invites = invites.filter(getattr(InvitationModel, field).like('%' + data.filters[field] + '%'))
            if data.order_type == 'desc':
                sort_param = getattr(InvitationModel, data.order_by).desc()
            else:
                sort_param = getattr(InvitationModel, data.order_by).asc()
            count = invites.count()
            invites = invites.order_by(sort_param).offset(data.page * data.page_size).limit(data.page_size).all()
        except Exception as e:
            error_msg = f'Error querying invite for listing in psql: {str(e)}'
            self._logger.error(error_msg)
            raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=error_msg)

        res.result = [i.to_dict() for i in invites]
        res.page = data.page
        res.num_of_pages = math.ceil(count / data.page_size)
        res.total = count
        return res.json_response()

    @router.put(
        '/invitation/{invite_id}',
        response_model=InvitationPOSTResponse,
        summary='update a single invite',
        tags=[_API_TAG]
    )
    def invitation_update(self, invite_id: str, data: InvitationPUT):
        self._logger.info('Called invitation_update')
        res = APIResponse()
        try:
            update_data = {}
            if data.status:
                update_data["status"] = data.status
            query = {"id": invite_id}
            db.session.query(InvitationModel).filter_by(**query).update(update_data)
            db.session.commit()
        except Exception as e:
            error_msg = f'Error updating invite in psql: {str(e)}'
            self._logger.error(error_msg)
            raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=error_msg)
        res.result = "success"
        return res.json_response()
