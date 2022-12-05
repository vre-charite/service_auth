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
from datetime import datetime
from datetime import timedelta
from unittest import mock

import keycloak

from app import create_app
from config import ConfigSettings
from module_keycloak.ops_admin import OperationsAdmin

EXCEPTION_DATA = {
    "response_body": '{ "error": "error" }',
    "error_message": '{ "error": "error" }',
    "response_code": 500,
}


@unittest.skip("deprecated the APIs")
class ResetTests(unittest.TestCase):

    def setUp(self):
        warnings.simplefilter("ignore", ResourceWarning)
        app = create_app()
        app.config['TESTING'] = True
        app.config['DEBUG'] = True
        self.app = app.test_client()

        operations_admin = OperationsAdmin(ConfigSettings.KEYCLOAK_REALM)
        try:
            # Delete the test user if it already exists
            operations_admin.delete_user("unittestuser")
        except keycloak.exceptions.KeycloakGetError:
            pass

        self.user = operations_admin.create_user(
            "unittestuser",
            "Testing1!",
            "unittesting@test.com",
            "Test",
            "User",
            cred_type="password",
            enabled=True
        )
        return super().setUp()

    @mock.patch("psycopg2.connect")
    @mock.patch("services.notifier_services.email_service.SrvEmail")
    def test_send_email(self, mock_connect, mock_email):
        mock_con = mock_connect.return_value
        mock_cur = mock_con.cursor.return_value
        mock_cur.fetchone.return_value = ""

        mock_email.send = ""

        data = {
            "username": "unittestuser",
            "realm": ConfigSettings.KEYCLOAK_REALM,
        }
        response = self.app.post('/v1/users/reset/send-email', json=data)
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.data)
        self.assertEqual(response_json["result"], "u*********g@****.***")

    def test_send_email_missing_info(self):
        data = {
            "realm": ConfigSettings.KEYCLOAK_REALM,
        }
        response = self.app.post('/v1/users/reset/send-email', json=data)
        self.assertEqual(response.status_code, 400)
        response_json = json.loads(response.data)
        self.assertEqual(response_json["result"], "Missing required information")

    @mock.patch.object(
        OperationsAdmin, '__init__', side_effect=keycloak.exceptions.KeycloakAuthenticationError(**EXCEPTION_DATA)
    )
    def test_send_email_keycloak_except(self, mock_connect):
        data = {
            "username": "unittestuser",
            "realm": ConfigSettings.KEYCLOAK_REALM,
        }
        response = self.app.post('/v1/users/reset/send-email', json=data)
        self.assertEqual(response.status_code, 500)
        response_json = json.loads(response.data)
        self.assertEqual(response_json["result"], 'SendResetEmail failed : 500: { "error": "error" }')

    @mock.patch("psycopg2.connect")
    def test_check_token(self, mock_connect):
        query_result = ["testing", "unittesting@test.com", datetime.now() + timedelta(1)]
        mock_con = mock_connect.return_value
        mock_cur = mock_con.cursor.return_value
        mock_cur.fetchone.return_value = query_result

        data = {
            "token": "testtoken",
            "realm": ConfigSettings.KEYCLOAK_REALM,
        }
        response = self.app.get('/v1/users/reset/check-token', query_string=data)
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.data)
        self.assertEqual(response_json["result"]["username"], "unittestuser")
        self.assertEqual(response_json["result"]["email"], "unittesting@test.com")

    @mock.patch("psycopg2.connect")
    def test_change_password(self, mock_connect):
        query_result = ["testing", "unittesting@test.com", datetime.now() + timedelta(1)]
        mock_con = mock_connect.return_value
        mock_cur = mock_con.cursor.return_value
        mock_cur.fetchone.return_value = query_result

        data = {
            "token": "testtoken",
            "password": "Testing234!",
            "realm": ConfigSettings.KEYCLOAK_REALM,
        }
        response = self.app.post('/v1/users/reset/password', json=data)
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.data)
        self.assertEqual(response_json["result"], "success")

    def test_change_password_missing_info(self):
        data = {
            "token": "testtoken",
            "realm": ConfigSettings.KEYCLOAK_REALM,
        }
        response = self.app.post('/v1/users/reset/password', json=data)
        self.assertEqual(response.status_code, 400)
        response_json = json.loads(response.data)
        self.assertEqual(response_json["result"], "Missing required information")
