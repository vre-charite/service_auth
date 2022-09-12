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

from keycloak import exceptions

test_user = {
    'username': 'test_user',
    'email': 'test_user',
    'id': 'test_user',
    'firstName': 'firstName',
    'lastName': 'lastName',
    'attributes': {'status': ['active']},
}


def test_get_user_info_by_id(test_client, mocker):
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_by_id', return_value=test_user.copy())
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_realm_roles', return_value=[])

    response = test_client.get('/v1/admin/user', params={'user_id': 'test_user'})
    assert response.status_code == 200


def test_get_user_info_by_username(test_client, mocker):
    mocker.patch(
        'app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_by_username', return_value=test_user.copy()
    )
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_realm_roles', return_value=[])

    response = test_client.get('/v1/admin/user', params={'username': 'test_user'})
    assert response.status_code == 200


def test_get_user_info_by_email(test_client, mocker):
    mocker.patch(
        'app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_by_email', return_value=test_user.copy()
    )
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_realm_roles', return_value=[])

    response = test_client.get('/v1/admin/user', params={'email': 'test_user'})
    assert response.status_code == 200


def test_get_user_with_admin_role(test_client, mocker):
    mocker.patch(
        'app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_by_email', return_value=test_user.copy()
    )
    mocker.patch(
        'app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_realm_roles',
        return_value=[{'name': 'platform-admin'}],
    )

    response = test_client.get('/v1/admin/user', params={'email': 'test_user'})
    assert response.status_code == 200
    assert response.json().get('result', {}).get('role') == 'admin'


def test_get_user_with_member_role(test_client, mocker):
    mocker.patch(
        'app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_by_email', return_value=test_user.copy()
    )
    mocker.patch(
        'app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_realm_roles',
        return_value=[{'name': 'not-admin'}],
    )

    response = test_client.get('/v1/admin/user', params={'email': 'test_user'})
    assert response.status_code == 200
    assert response.json().get('result', {}).get('role') == 'member'


def test_get_user_info_missing_params(test_client):
    response = test_client.get('/v1/admin/user')
    assert response.status_code == 400
    assert response.json().get('error_msg') == 'One of email, username, user_id is mandetory'


def test_get_user_info_user_not_found(test_client, mocker):

    m = mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_by_id')
    m.side_effect = exceptions.KeycloakGetError

    response = test_client.get('/v1/admin/user', params={'user_id': 'test_user'})
    assert response.status_code == 404
    assert response.json().get('error_msg') == 'user not found'


def test_update_user_attribute(test_client, mocker):
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_id', return_value=test_user.copy())
    mocker.patch(
        'app.resources.keycloak_api.ops_admin.OperationsAdmin.update_user_attributes',
        return_value={'test_attribute': 'test_value'},
    )

    response = test_client.put(
        '/v1/admin/user',
        json={
            'last_login': True,
            'username': 'test_user',
            'announcement': {'project_code': 'test_project', 'announcement_pk': '111'},
        },
    )
    assert response.status_code == 200
    assert response.json().get('result') == {'test_attribute': 'test_value'}


def test_update_user_attribute_missing_username(test_client, mocker):
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_id', return_value=test_user.copy())
    mocker.patch(
        'app.resources.keycloak_api.ops_admin.OperationsAdmin.update_user_attributes',
        return_value={'test_attribute': 'test_value'},
    )

    response = test_client.put(
        '/v1/admin/user',
        json={'last_login': True, 'announcement': {'project_code': 'test_project', 'announcement_pk': '111'}},
    )
    assert response.status_code == 422


def test_update_user_attribute_missing_updated_attrs(test_client, mocker):
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_id', return_value=test_user.copy())
    mocker.patch(
        'app.resources.keycloak_api.ops_admin.OperationsAdmin.update_user_attributes',
        return_value={'test_attribute': 'test_value'},
    )

    response = test_client.put('/v1/admin/user', json={'username': 'test'})
    assert response.status_code == 400
    assert response.json().get('error_msg') == 'last_login or announcement is required'


# keycloak group operation


def test_add_user_to_keycloak_new_group(test_client, mocker):
    new_group = {'name': 'test_new_group', 'id': 'test_id'}
    user_id = 'test_user_id'

    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_id', return_value=user_id)
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_group_by_name', return_value=None)
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.create_group')
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_group_by_name', return_value=new_group)
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.add_user_to_group')

    response = test_client.post('/v1/admin/users/group', json={'username': 'test_user', 'groupname': 'test_group'})
    assert response.status_code == 200


def test_add_user_to_keycloak_existing_group(test_client, mocker):
    existing_group = {'name': 'test_new_group', 'id': 'test_id'}
    user_id = 'test_user_id'

    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_id', return_value=user_id)
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_group_by_name', return_value=existing_group)
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.add_user_to_group')

    response = test_client.post('/v1/admin/users/group', json={'username': 'test_user', 'groupname': 'test_group'})
    assert response.status_code == 200


def test_add_user_to_keycloak_group_missing_payload(test_client):

    response = test_client.post(
        '/v1/admin/users/group',
        json={
            'username': 'test_user',
        },
    )
    assert response.status_code == 422


def test_remove_user_to_keycloak_existing_group(test_client, mocker):
    existing_group = {'name': 'test_new_group', 'id': 'test_id'}
    user_id = 'test_user_id'

    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_id', return_value=user_id)
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_group_by_name', return_value=existing_group)
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.remove_user_from_group')

    response = test_client.delete('/v1/admin/users/group', params={'username': 'test_user', 'groupname': 'test_group'})
    assert response.status_code == 200


def test_remove_user_to_keycloak_group_missing_params(test_client):

    response = test_client.delete('/v1/admin/users/group', params={})
    assert response.status_code == 422


# test list users under roles


def create_test_user_list(size=10):
    user_list = []
    for x in range(size):
        user_list.append(
            {
                'username': 'test_user_%d' % x,
                'email': 'test_user_%d@email.com' % x,
                'id': 'test_user_%d' % x,
                'firstName': 'firstName_%d' % x,
                'lastName': 'lastName_%d' % x,
                'attributes': {'status': ['active']},
            }
        )

    return user_list


def test_list_users_under_roles_pagination_1(test_client, mocker):
    num_of_user = 20
    page_size = 10
    users = create_test_user_list(num_of_user)

    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_users_in_role', return_value=users)

    response = test_client.post(
        '/v1/admin/roles/users',
        json={
            'role_names': ['test-admin'],
            page_size: page_size,
        },
    )
    assert response.status_code == 200
    assert response.json().get('num_of_pages') == num_of_user / page_size
    assert response.json().get('total') == num_of_user


def test_list_users_under_roles_pagination_2(test_client, mocker):
    num_of_user = 20
    page_size = 5
    users = create_test_user_list(num_of_user)

    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_users_in_role', return_value=users)

    response = test_client.post(
        '/v1/admin/roles/users',
        json={
            'role_names': ['test-admin'],
            'page_size': page_size,
        },
    )
    assert response.status_code == 200
    assert response.json().get('num_of_pages') == num_of_user / page_size
    assert response.json().get('total') == num_of_user


def test_list_users_under_roles_filter_by_name(test_client, mocker):
    num_of_user = 10
    users = create_test_user_list(num_of_user)

    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_users_in_role', return_value=users)

    response = test_client.post(
        '/v1/admin/roles/users',
        json={
            'role_names': ['test-admin'],
            'username': 'test_user_1',
        },
    )
    assert response.status_code == 200
    assert len(response.json().get('result')) == 1


def test_list_users_under_roles_filter_by_email(test_client, mocker):
    num_of_user = 10
    users = create_test_user_list(num_of_user)

    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_users_in_role', return_value=users)

    response = test_client.post(
        '/v1/admin/roles/users',
        json={
            'role_names': ['test-admin'],
            'email': 'test_user_3@email.com',
        },
    )
    assert response.status_code == 200
    assert len(response.json().get('result')) == 1


def test_list_users_under_roles_filter_order_by_email(test_client, mocker):
    num_of_user = 10
    users = create_test_user_list(num_of_user)

    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_users_in_role', return_value=users)

    response = test_client.post(
        '/v1/admin/roles/users', json={'role_names': ['test-admin'], 'order_by': 'email', 'order_type': 'desc'}
    )
    assert response.status_code == 200
    user_list = response.json().get('result')
    assert user_list[0].get('email') > user_list[1].get('email')


def test_list_users_under_roles_filter_order_by_username(test_client, mocker):
    num_of_user = 10
    users = create_test_user_list(num_of_user)

    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_users_in_role', return_value=users)

    response = test_client.post(
        '/v1/admin/roles/users', json={'role_names': ['test-admin'], 'order_by': 'name', 'order_type': 'desc'}
    )
    assert response.status_code == 200
    user_list = response.json().get('result')
    assert user_list[0].get('name') > user_list[1].get('name')
