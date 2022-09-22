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

def test_user_add_ad_group(test_client, mocker):
    mocker.patch('app.services.data_providers.ldap_client.LdapClient.get_user_by_email', return_value=(None, None))
    mocker.patch('app.services.data_providers.ldap_client.LdapClient.format_group_dn')
    mocker.patch('app.services.data_providers.ldap_client.LdapClient.add_user_to_group')

    response = test_client.put(
        '/v1/user/ad-group',
        json={
            'user_email': 'test_email',
            'group_code': 'test_group',
            'operation_type': 'add',
        },
    )
    assert response.status_code == 200
    assert response.json().get('result') == '%s user %s from ad group' % ('add', 'test_email')


def test_user_remove_ad_group(test_client, mocker):
    mocker.patch('app.services.data_providers.ldap_client.LdapClient.get_user_by_email', return_value=(None, None))
    mocker.patch('app.services.data_providers.ldap_client.LdapClient.format_group_dn')
    mocker.patch('app.services.data_providers.ldap_client.LdapClient.remove_user_from_group')

    response = test_client.put(
        '/v1/user/ad-group',
        json={
            'user_email': 'test_email',
            'group_code': 'test_group',
            'operation_type': 'remove',
        },
    )
    assert response.status_code == 200
    assert response.json().get('result') == '%s user %s from ad group' % ('remove', 'test_email')


# disable/enable user
def test_user_enable(test_client, mocker):
    mocker.patch(
        'app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_by_email', return_value={'id': 'test_user_id'}
    )
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.update_user_attributes', return_value='')

    response = test_client.put(
        '/v1/user/account',
        json={
            'user_email': 'test_email',
            'operation_type': 'enable',
        },
    )
    print(response.json())
    assert response.status_code == 200
    assert response.json().get('result') == '%s user %s' % ('enable', 'test_email')


def test_user_disable(test_client, mocker):
    mocker.patch(
        'app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_by_email', return_value={'id': 'test_user_id'}
    )
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.update_user_attributes', return_value='')

    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.get_user_realm_roles', return_value=[])
    mocker.patch('app.resources.keycloak_api.ops_admin.OperationsAdmin.remove_user_realm_roles', return_value='')

    mocker.patch(
        'app.services.data_providers.ldap_client.LdapClient.get_user_by_email', return_value=(None, {'memberOf': []})
    )

    response = test_client.put(
        '/v1/user/account',
        json={
            'user_email': 'test_email',
            'operation_type': 'disable',
        },
    )
    assert response.status_code == 200
    assert response.json().get('result') == '%s user %s' % ('disable', 'test_email')
