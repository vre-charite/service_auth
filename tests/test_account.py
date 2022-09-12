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

def test_user_account_duplicate(test_client, mocker):
    mocker.patch('app.routers.accounts.AccountRequest.is_duplicate_user', return_value=True)

    response = test_client.post('/v1/accounts', json={'email': 'test_email', 'username': 'test_user'})
    assert response.status_code == 400


def test_user_account_user_dn_not_found(test_client, mocker):
    mocker.patch('app.routers.accounts.AccountRequest.is_duplicate_user', return_value=False)
    mocker.patch('app.services.data_providers.ldap_client.LdapClient.get_user_by_username', return_value=(None, None))
    mocker.patch('app.services.notifier_services.email_service.SrvEmail.send')
    mocker.patch('app.services.notifier_services.email_service.SrvEmail.send')

    response = test_client.post('/v1/accounts', json={'email': 'test_email', 'username': 'test_user'})
    assert response.status_code == 200
    assert response.json().get('result') == 'Request for a test account is under review'


def test_user_account_user_dn_exist(test_client, mocker):
    mocker.patch('app.routers.accounts.AccountRequest.is_duplicate_user', return_value=False)
    mocker.patch(
        'app.services.data_providers.ldap_client.LdapClient.get_user_by_username',
        return_value=(
            'user_dn',
            {
                'mail': [b'test_email'],
                'givenName': [b'test_user'],
                'sn': [b'test_user'],
            },
        ),
    )

    mocker.patch('app.services.data_providers.ldap_client.LdapClient.add_user_to_group')
    mocker.patch('app.services.data_providers.ldap_client.LdapClient.add_user_to_group')

    mocker.patch('app.services.notifier_services.email_service.SrvEmail.send')
    mocker.patch('app.services.notifier_services.email_service.SrvEmail.send')

    response = test_client.post('/v1/accounts', json={'email': 'test_email', 'username': 'test_user'})
    assert response.status_code == 200
    assert response.json().get('result') == 'Request for a test account has been approved'


def test_user_account_email_not_match(test_client, mocker):
    mocker.patch('app.routers.accounts.AccountRequest.is_duplicate_user', return_value=False)
    mocker.patch(
        'app.services.data_providers.ldap_client.LdapClient.get_user_by_username',
        return_value=(
            'user_dn',
            {
                'mail': [b'test_email_not_matched'],
                'givenName': [b'test_user'],
                'sn': [b'test_user'],
            },
        ),
    )

    mocker.patch('app.services.data_providers.ldap_client.LdapClient.add_user_to_group')
    mocker.patch('app.services.data_providers.ldap_client.LdapClient.add_user_to_group')

    mocker.patch('app.services.notifier_services.email_service.SrvEmail.send')
    mocker.patch('app.services.notifier_services.email_service.SrvEmail.send')

    response = test_client.post('/v1/accounts', json={'email': 'test_email', 'username': 'test_user'})
    assert response.status_code == 200
    assert response.json().get('result') == 'Request for a test account is under review'
