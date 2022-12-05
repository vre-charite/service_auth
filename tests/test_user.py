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
import unittest
import warnings
from unittest import mock

import keycloak
from keycloak import exceptions

from tests.prepare_test import SetupTest
from tests.logger import Logger

from app import create_app
from config import ConfigSettings
from module_keycloak.ops_admin import OperationsAdmin
from module_keycloak.ops_user import OperationsUser

EXCEPTION_DATA = {
    "response_body": '{ "error": "error" }',
    "error_message": '{ "error": "error" }',
    "response_code": 500,
}


class UserTests(unittest.TestCase):
    AUTH_DATA = {
        "realm": ConfigSettings.KEYCLOAK_REALM,
        "username": "unittestuser",
        "password": "Testing123!",
    }

    log = Logger(name='test_user_apis.log')
    test = SetupTest(log)

    @classmethod
    def setUpClass(self):
        warnings.simplefilter("ignore", ResourceWarning)
        # app = create_app()

        # app.config['TESTING'] = True
        # app.config['DEBUG'] = True
        self.app = self.test.app

        operations_admin = OperationsAdmin(ConfigSettings.KEYCLOAK_REALM)
        try:
            # Delete the test user if it already exists
            operations_admin.delete_user("unittestuser")
        except keycloak.exceptions.KeycloakGetError:
            pass

        self.user = operations_admin.create_user(
            "unittestuser",
            "Testing123!",
            "unittesting@test.com",
            "Test",
            "User",
            cred_type="password",
            enabled=True
        )

        print(self.user)

        # return super().setUp()

    @classmethod
    def tearDownClass(self):
        operations_admin = OperationsAdmin(ConfigSettings.KEYCLOAK_REALM)
        operations_admin.delete_user(self.user)
        # return super().tearDown()

    def test_docs(self):
        response = self.app.get('/v1/api-doc')
        self.assertEqual(response.status_code, 200)

    def test_user_auth(self):
        response = self.app.post('/v1/users/auth', json=self.AUTH_DATA)
        print(response.json())
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json["error_msg"], "")
        self.assertTrue(response_json["result"]["access_token"])

    def test_auth_missing(self):
        data = self.AUTH_DATA.copy()
        del data["password"]
        response = self.app.post('/v1/users/auth', json=data)
        print(response.json())
        self.assertEqual(response.status_code, 422)


    @mock.patch.object(OperationsUser, '__init__',
                       side_effect=keycloak.exceptions.KeycloakAuthenticationError(**EXCEPTION_DATA))
    def test_auth_keycloakauth_exception(self, mock_data):
        response = self.app.post('/v1/users/auth', json=self.AUTH_DATA)
        print(response.json())
        self.assertEqual(response.status_code, 401)
        response_json = response.json()
        self.assertEqual(response_json.get("error_msg"), '500: { "error": "error" }')


    @mock.patch.object(OperationsUser, '__init__', side_effect=keycloak.exceptions.KeycloakGetError(**EXCEPTION_DATA))
    def test_auth_keycloakget_exception(self, mock_data):
        response = self.app.post('/v1/users/auth', json=self.AUTH_DATA)
        self.assertEqual(response.status_code, 401)
        response_json = response.json()
        self.assertEqual(response_json.get("error_msg"), '500: { "error": "error" }')

    @mock.patch.object(OperationsUser, '__init__', side_effect=Exception())
    def test_auth_exception(self, mock_data):
        response = self.app.post('/v1/users/auth', json=self.AUTH_DATA)
        self.assertEqual(response.status_code, 500)
        response_json = response.json()
        print(response_json)
        self.assertEqual(response_json.get("error_msg"), "User authentication failed : ")

    def test_user_refresh(self):
        response = self.app.post('/v1/users/auth', json=self.AUTH_DATA)
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        refresh_data = {
            "realm": ConfigSettings.KEYCLOAK_REALM,
            "refreshtoken": response_json["result"]["refresh_token"]
        }
        response = self.app.post('/v1/users/refresh', json=refresh_data)
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json.get("error_msg"), "")
        self.assertTrue(response_json["result"]["refresh_token"])

    def test_user_refresh_missing(self):
        response = self.app.post('/v1/users/refresh')
        self.assertEqual(response.status_code, 422)


    @mock.patch.object(OperationsUser, '__init__', side_effect=keycloak.exceptions.KeycloakGetError(**EXCEPTION_DATA))
    def test_refresh_keycloakget_exception(self, mock_data):
        refresh_data = {
            "realm": ConfigSettings.KEYCLOAK_REALM,
            "refreshtoken": "test"
        }
        response = self.app.post('/v1/users/refresh', json=refresh_data)
        self.assertEqual(response.status_code, 500)
        response_json = response.json()
        self.assertEqual(response_json.get("error_msg"), '500: { "error": "error" }')

    @unittest.skip("deprecated the APIs")
    def test_user_password(self):
        data = {
            "username": "unittestuser",
            "old_password": "Testing123!",
            "new_password": "Testing234!",
            "realm": ConfigSettings.KEYCLOAK_REALM,
        }
        response = self.app.put('/v1/users/password', json=data)
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json.get("error_msg"), "success")

        auth_data = {
            "username": "unittestuser",
            "password": "Testing234!",
            "realm": ConfigSettings.KEYCLOAK_REALM,
        }
        response = self.app.post('/v1/users/auth', json=auth_data)
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json.get("error_msg"), "")
        self.assertTrue(response_json["result"]["access_token"])

        # Change the password back so it's consistant for other tests
        data["old_password"] = "Testing234!"
        data["new_password"] = "Testing123!"
        response = self.app.put('/v1/users/password', json=data)
        self.assertEqual(response.status_code, 200)

    @unittest.skip("deprecated the APIs")
    def test_password_missing(self):
        data = {
            "username": "unittestuser",
            "new_password": "Testing234!",
            "realm": ConfigSettings.KEYCLOAK_REALM,
        }
        response = self.app.put('/v1/users/password', json=data)
        self.assertEqual(response.status_code, 422)

    @unittest.skip("deprecated the APIs")
    def test_password_insecure(self):
        data = {
            "username": "unittestuser",
            "old_password": "Testing123!",
            "new_password": "test",
            "realm": ConfigSettings.KEYCLOAK_REALM,
        }
        response = self.app.put('/v1/users/password', json=data)
        self.assertEqual(response.status_code, 406)
        response_json = response.json()
        self.assertEqual(response_json.get("error_msg"), "invalid new password")

    @unittest.skip("deprecated the APIs")
    # @mock.patch.object(OperationsUser, '__init__', side_effect=Exception())
    def test_password_user_exception(self, mock_data):
        data = {
            "username": "unittestuser",
            "old_password": "Testing123!",
            "new_password": "Testing234!",
            "realm": ConfigSettings.KEYCLOAK_REALM,
        }
        response = self.app.put('/v1/users/password', json=data)
        self.assertEqual(response.status_code, 400)
        response_json = response.json()
        self.assertEqual(response_json.get("error_msg"), "incorrect realm, username or old password: ")

    @unittest.skip("deprecated the APIs")
    # @mock.patch.object(OperationsAdmin, '__init__', side_effect=Exception())
    def test_password_admin_exception(self, mock_data):
        data = {
            "username": "unittestuser",
            "old_password": "Testing123!",
            "new_password": "Testing234!",
            "realm": ConfigSettings.KEYCLOAK_REALM,
        }
        response = self.app.put('/v1/users/password', json=data)
        self.assertEqual(response.status_code, 500)
        response_json = response.json()
        self.assertEqual(response_json.get("error_msg"), 'invalid admin credentials: ')

    @unittest.skip("deprecated the APIs")
    # @mock.patch.object(OperationsAdmin, 'get_user_id', side_effect=Exception())
    def test_password_get_user_exception(self, mock_data):
        data = {
            "username": "unittestuser",
            "old_password": "Testing123!",
            "new_password": "Testing234!",
            "realm": ConfigSettings.KEYCLOAK_REALM,
        }
        response = self.app.put('/v1/users/password', json=data)
        self.assertEqual(response.status_code, 500)
        response_json = response.json()
        self.assertEqual(response_json.get("error_msg"), 'cannot get user id: ')

    def test_user_status(self):
        data = {
            "email": "jiayu.zhang015+10@gmail.com",
        }
        response = self.app.get('/v1/user/status', params=data)
        self.assertEqual(response.status_code, 200)
        res = response.json().get("result")
        self.assertEqual(res.get("email"), "jiayu.zhang015+10@gmail.com")
        self.assertTrue(res.get("status") in ["active", "disabled", "hibernate"])

    def test_user_status_missing_email(self):
        data = {
        }
        response = self.app.get('/v1/user/status', params=data)
        self.assertEqual(response.status_code, 422)

    def test_user_status_bad_email(self):
        data = {
            "email": "afakeemailthatcertainlydoesnotexist@fake.ca",
        }
        response = self.app.get('/v1/user/status', params=data)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json().get("error_msg"), "User not exists")


if __name__ == "__main__":
    unittest.main(warnings='ignore')
