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

import time

import mock
import pytest

from app.config import ConfigSettings
from app.resources.keycloak_api.ops_admin import OperationsAdmin

user_json = {
    'email': 'testuser@example.com',
    'enabled': True,
    'first_name': 'test',
    'id': 'fake-user-id',
    'last_name': 'user',
    'name': 'testuser',
    'role': 'member',
    'username': 'testuser',
    'attributes': {'status': ['active']},
}


def ldap_mock_client(monkeypatch, user_exists):
    from app.services.data_providers.ldap_client import LdapClient

    class LdapClientMock:
        def __init__(self, user_data={}, user_exists=user_exists):
            self.user_data = user_data
            self.user_exists = user_exists

        def is_account_in_ad(self, email):
            return True

        def format_group_dn(self, group_name):
            return group_name

        def get_user_by_email(self, email):
            return 'user_dn', self.user_data

        def add_user_to_group(self, user_dn, group_dn):
            return ''

    ldap_mock_client = LdapClientMock(
        user_data={'username': 'testuser', 'email': 'testuser@example.com'}, user_exists=user_exists
    )
    monkeypatch.setattr(LdapClient, 'is_account_in_ad', ldap_mock_client.is_account_in_ad)
    monkeypatch.setattr(LdapClient, 'format_group_dn', ldap_mock_client.format_group_dn)
    monkeypatch.setattr(LdapClient, 'get_user_by_email', ldap_mock_client.get_user_by_email)
    monkeypatch.setattr(LdapClient, 'add_user_to_group', ldap_mock_client.add_user_to_group)


@pytest.fixture
def ldap_mock(monkeypatch):
    return ldap_mock_client(monkeypatch, True)


@pytest.fixture
def ldap_mock_no_user(monkeypatch):
    return ldap_mock_client(monkeypatch, False)


@pytest.mark.dependency()
@mock.patch.object(OperationsAdmin, 'get_user_by_email', side_effect=None)
def test_create_invitation_exists_in_ad(get_user_mock, test_client, httpx_mock, ldap_mock):
    get_user_mock.return_value = None  # {"username": "testuser", "email": "testuser@example.com"}
    httpx_mock.add_response(
        method='POST',
        url=ConfigSettings.NEO4J_SERVICE + 'nodes/Container/query',
        json=[
            {
                'global_entity_id': 'fakeprojectgeid',
                'name': 'Fake Project',
                'code': 'fakeproject',
            }
        ],
        status_code=200,
    )
    httpx_mock.add_response(
        method='POST', url=ConfigSettings.EMAIL_SERVICE, json={'result': 'success'}, status_code=200
    )
    payload = {
        'email': 'test1@example.com',
        'platform_role': 'member',
        'relationship': {
            'project_geid': 'fakeprojectgeid',
            'project_role': 'admin',
            'inviter': 'admin',
        },
        'invited_by': 'admin',
    }
    response = test_client.post('/v1/invitations', json=payload)
    assert response.status_code == 200


@pytest.mark.dependency()
@mock.patch.object(OperationsAdmin, 'get_user_by_email', side_effect=None)
def test_create_invitation_no_ad(get_user_mock, test_client, httpx_mock, ldap_mock_no_user):
    get_user_mock.return_value = None
    httpx_mock.add_response(
        method='POST',
        url=ConfigSettings.NEO4J_SERVICE + 'nodes/Container/query',
        json=[
            {
                'global_entity_id': 'fakeprojectgeid',
                'name': 'Fake Project',
                'code': 'fakeproject',
            }
        ],
        status_code=200,
    )
    httpx_mock.add_response(
        method='POST', url=ConfigSettings.EMAIL_SERVICE, json={'result': 'success'}, status_code=200
    )
    payload = {
        'email': 'test2@example.com',
        'platform_role': 'member',
        'relationship': {
            'project_geid': 'fakeprojectgeid',
            'project_role': 'admin',
            'inviter': 'admin',
        },
        'invited_by': 'admin',
    }
    response = test_client.post('/v1/invitations', json=payload)
    assert response.status_code == 200


@mock.patch.object(OperationsAdmin, 'get_user_by_email', side_effect=None)
def test_create_invitation_no_relation(get_user_mock, test_client, httpx_mock, ldap_mock_no_user):
    get_user_mock.return_value = None
    httpx_mock.add_response(
        method='POST', url=ConfigSettings.EMAIL_SERVICE, json={'result': 'success'}, status_code=200
    )
    payload = {'email': 'test3@example.com', 'platform_role': 'member', 'invited_by': 'admin'}
    response = test_client.post('/v1/invitations', json=payload)
    assert response.status_code == 200


@mock.patch.object(OperationsAdmin, 'get_user_by_email', side_effect=None)
def test_create_invitation_admin(get_user_mock, test_client, httpx_mock, ldap_mock_no_user):
    get_user_mock.return_value = None
    httpx_mock.add_response(
        method='POST', url=ConfigSettings.EMAIL_SERVICE, json={'result': 'success'}, status_code=200
    )
    payload = {'email': 'test4@example.com', 'platform_role': 'admin', 'invited_by': 'admin'}
    response = test_client.post('/v1/invitations', json=payload)
    assert response.status_code == 200


@pytest.mark.dependency(depends=['test_create_invitation_admin'])
@mock.patch.object(OperationsAdmin, 'get_user_by_email', side_effect={'user': 'user'})
def test_create_invitation_admin_already_exists(get_user_mock, test_client, httpx_mock, ldap_mock):
    payload = {'email': 'test4@example.com', 'platform_role': 'admin', 'invited_by': 'admin'}
    response = test_client.post('/v1/invitations', json=payload)
    assert response.status_code == 400
    assert response.json()['result'] == '[ERROR] User already exists in platform'


@pytest.mark.dependency(depends=['test_create_invitation_no_ad'])
@mock.patch.object(OperationsAdmin, 'get_user_by_email', side_effect={'user': 'user'})
def test_create_invitation_already_exists_in_project(get_user_mock, test_client, httpx_mock, ldap_mock):
    httpx_mock.add_response(
        method='POST',
        url=ConfigSettings.NEO4J_SERVICE + 'nodes/Container/query',
        json=[
            {
                'global_entity_id': 'fakeprojectgeid',
                'name': 'Fake Project',
                'code': 'fakeproject',
            }
        ],
        status_code=200,
    )
    payload = {
        'email': 'test2@example.com',
        'platform_role': 'member',
        'relationship': {
            'project_geid': 'fakeprojectgeid',
            'project_role': 'admin',
            'inviter': 'admin',
        },
        'invited_by': 'admin',
    }
    response = test_client.post('/v1/invitations', json=payload)
    assert response.status_code == 409
    assert response.json()['result'] == 'Invitation for this user already exists'


@pytest.mark.dependency(depends=['test_create_invitation_exists_in_ad'])
def test_get_invite_list(test_client, httpx_mock):
    payload = {
        'page': 0,
        'page_size': 1,
        'filters': {
            'project_id': 'fakeprojectgeid',
        },
    }
    response = test_client.post('/v1/invitation-list', json=payload)
    assert response.status_code == 200
    assert response.json()['result'][0]['project_id'] == 'fakeprojectgeid'


@pytest.mark.dependency(depends=['test_create_invitation_exists_in_ad'])
def test_get_invite_list_filter(test_client, httpx_mock):
    payload = {
        'page': 0,
        'page_size': 1,
        'filters': {
            'email': 'example.com',
        },
    }
    response = test_client.post('/v1/invitation-list', json=payload)
    assert response.status_code == 200
    assert response.json()['result'][0]['project_id'] == 'fakeprojectgeid'


@mock.patch.object(OperationsAdmin, 'get_user_by_email', side_effect=None)
@pytest.mark.dependency(depends=['test_create_invitation_exists_in_ad'])
def test_get_invite_list_order(get_user_mock, test_client, httpx_mock):
    get_user_mock.return_value = None
    timestamp = time.time()
    httpx_mock.add_response(
        method='POST', url=ConfigSettings.EMAIL_SERVICE, json={'result': 'success'}, status_code=200
    )
    payload = {'email': f'a@ordertest_{timestamp}.com', 'platform_role': 'admin', 'invited_by': 'admin'}
    response = test_client.post('/v1/invitations', json=payload)
    assert response.status_code == 200
    payload = {'email': f'b@ordertest_{timestamp}.com', 'platform_role': 'admin', 'invited_by': 'admin'}
    response = test_client.post('/v1/invitations', json=payload)
    assert response.status_code == 200
    payload = {'email': f'c@ordertest_{timestamp}.com', 'platform_role': 'admin', 'invited_by': 'admin'}
    response = test_client.post('/v1/invitations', json=payload)
    assert response.status_code == 200

    payload = {
        'page': 0,
        'page_size': 5,
        'order_by': 'email',
        'order_type': 'desc',
        'filters': {
            'email': f'ordertest_{timestamp}.com',
        },
    }
    response = test_client.post('/v1/invitation-list', json=payload)
    assert response.status_code == 200
    assert len(response.json()['result']) == 3
    assert response.json()['result'][0]['email'] == f'c@ordertest_{timestamp}.com'
    assert response.json()['result'][1]['email'] == f'b@ordertest_{timestamp}.com'
    assert response.json()['result'][2]['email'] == f'a@ordertest_{timestamp}.com'


@mock.patch.object(OperationsAdmin, 'get_user_by_email', side_effect=[user_json])
@mock.patch.object(OperationsAdmin, 'get_user_realm_roles', side_effect=[[{'name': 'fakeproject-admin'}]])
def test_check_invite_email(get_user_mock, realm_roles_mock, test_client, httpx_mock):
    httpx_mock.add_response(
        method='POST',
        url=ConfigSettings.NEO4J_SERVICE + 'nodes/Container/query',
        json=[
            {
                'global_entity_id': 'fakeprojectgeid',
                'name': 'Fake Project',
                'code': 'fakeproject',
            }
        ],
        status_code=200,
    )
    payload = {
        'project_geid': 'fakeprojectgeid',
    }
    response = test_client.get('/v1/invitation/check/testuser@example.com', params=payload)
    assert response.status_code == 200
    assert response.json()['result']['role'] == user_json['role']
    assert response.json()['result']['relationship']['project_geid'] == 'fakeprojectgeid'


@mock.patch.object(OperationsAdmin, 'get_user_by_email', side_effect=[user_json])
@mock.patch.object(OperationsAdmin, 'get_user_realm_roles', side_effect=[[{'name': 'fakeproject-admin'}]])
def test_check_invite_email_bad_project_id(get_user_mock, realm_roles_mock, test_client, httpx_mock):
    httpx_mock.add_response(
        method='POST', url=ConfigSettings.NEO4J_SERVICE + 'nodes/Container/query', json=[], status_code=200
    )
    payload = {
        'project_geid': 'fakeprojectgeid',
    }
    response = test_client.get('/v1/invitation/check/testuser@example.com', params=payload)
    assert response.status_code == 404
    assert response.json()['error_msg'] == 'Project not found: fakeprojectgeid'


@mock.patch.object(OperationsAdmin, 'get_user_by_email', side_effect=[user_json])
@mock.patch.object(OperationsAdmin, 'get_user_realm_roles', side_effect=[[]])
def test_check_invite_email_no_relation(get_user_mock, realm_roles_mock, test_client, httpx_mock):
    httpx_mock.add_response(
        method='POST',
        url=ConfigSettings.NEO4J_SERVICE + 'nodes/Container/query',
        json=[
            {
                'global_entity_id': 'fakeprojectgeid',
                'name': 'Fake Project',
                'code': 'fakeproject',
            }
        ],
        status_code=200,
    )
    payload = {
        'project_geid': 'fakeprojectgeid',
    }
    response = test_client.get('/v1/invitation/check/testuser@example.com', params=payload)
    assert response.status_code == 200
    assert response.json()['result']['role'] == user_json['role']
    assert response.json()['result']['relationship'] == {}


@mock.patch.object(OperationsAdmin, 'get_user_by_email', side_effect=[user_json])
@mock.patch.object(OperationsAdmin, 'get_user_realm_roles', side_effect=[[{'name': 'platform-admin'}]])
def test_check_invite_email_platform_admin(get_user_mock, realm_roles_mock, test_client, httpx_mock):
    httpx_mock.add_response(
        method='POST', url=ConfigSettings.NEO4J_SERVICE + 'nodes/Container/query', json=[{}], status_code=200
    )
    payload = {
        'project_geid': 'fakeprojectgeid',
    }
    response = test_client.get('/v1/invitation/check/testuser@example.com', params=payload)
    assert response.status_code == 200
    assert response.json()['result']['role'] == 'admin'
    assert response.json()['result']['relationship'] == {}

@mock.patch.object(OperationsAdmin, 'get_user_realm_roles', side_effect=[[{'name': 'platform-admin'}]])
@mock.patch.object(OperationsAdmin, 'get_user_by_email', side_effect=None)
def test_check_invite_no_user(get_user_mock, realm_roles_mock, test_client, httpx_mock):
    get_user_mock.return_value = None
    payload = {
        'project_geid': 'fakeprojectgeid',
    }
    response = test_client.get('/v1/invitation/check/testuser@example.com', params=payload)
    assert response.status_code == 404
    assert response.json()['error_msg'] == 'User not found in keycloak'
