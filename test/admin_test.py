import unittest
from unittest import mock
import json
import requests
import keycloak
from keycloak import exceptions
import warnings
import psycopg2
from datetime import datetime, timedelta 

from config import ConfigClass
from app import create_app
from module_keycloak.ops_admin import OperationsAdmin
from module_keycloak.ops_user import OperationsUser


class AdminTests(unittest.TestCase):

    def setUp(self):
        warnings.simplefilter("ignore", ResourceWarning)
        app = create_app()

        app.config['TESTING'] = True
        app.config['DEBUG'] = True
        self.app = app.test_client()

        operations_admin = OperationsAdmin("vre")
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
            cred_type = "password",
            enabled = True
        )
        return super().setUp()

    def test_create_user(self):
        data = {
            "username": "unittestuser2",
            "password": "Testing1!",
            "email": "unittesting2@test.com",
            "firstname": "Test",
            "lastname": "Test",
            "realm": "vre"
        }
        response = self.app.post('/v1/admin/users', json=data)
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.data)
        self.assertEqual(response_json["error_msg"], "")
        self.assertEqual(response_json["result"], "User created successfully")

        operations_admin = OperationsAdmin("vre")
        user_id = operations_admin.get_user_id("unittestuser2")
        operations_admin.delete_user(user_id)

    @mock.patch("psycopg2.connect")
    def test_get_username(self, mock_connect):
        query_result = ["testing", "data", datetime.now() + timedelta(1), datetime.now() + timedelta(1)]
        mock_con = mock_connect.return_value
        mock_cur = mock_con.cursor.return_value
        mock_cur.fetchone.return_value = query_result

        data = {
            "username": "unittestuser",
            "invite_code": "testing",
            "realm": "vre",
        }
        print(data)
        response = self.app.get('/v1/users/name', query_string=data)
        print(response.data)
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.data)
        self.assertEqual(response_json["error_msg"], "")
        self.assertEqual(response_json["result"]["username"], "unittestuser")


    def test_get_email(self):
        data = {
            "email": "unittesting@test.com",
            "realm": "vre"
        }
        response = self.app.get('/v1/admin/users/email', query_string=data)
        response_json = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_json["error_msg"], "")
        self.assertEqual(response_json["result"]["username"], "unittestuser")
