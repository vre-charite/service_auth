from flask import request
from flask_restx import Api, Resource, fields
from models.api_response import APIResponse, EAPIResponseCode
from services.data_providers.ldap_client import LdapClient
from services.data_providers.neo4j_client import Neo4jClient
from services.notifier_services.email_service import SrvEmail
from config import ConfigClass
from resources.utils import fetch_geid, get_formatted_datetime
from resources.error_handler import APIException
from services.logger_services.logger_factory_service import SrvLoggerFactory
import requests

logger = SrvLoggerFactory('test_accounts').get_logger()

class AccountRequest(Resource):

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
                    "code": ConfigClass.TEST_PROJECT_CODE,
                }
            }
            response = requests.post(ConfigClass.NEO4J_SERVICE + "relations/query", json=payload)
            if response.json():
                error_msg = f"User already exists in Neo4j in test project: {username}"
                logger.error(error_msg)
                raise APIException(
                    status_code=EAPIResponseCode.conflict.value,
                    error_msg=error_msg
                )
            else:
                # User exists in VRE but is not in test project
                notes = """
                This user is already a VRE user, and submitted a request for a VRE Test Account from the VRE Portal. 
                Please contact the user to determine further action.
                """
                email_service = SrvEmail()
                email_service.send(
                    subject="Action Required: Existing VRE user requested VRE Test Account",
                    receiver=ConfigClass.EMAIL_SUPPORT,
                    sender=ConfigClass.EMAIL_SUPPORT,
                    msg_type="html",
                    template="test_account/support_notification.html",
                    template_kwargs={
                        "title": "VRE test account request pending review",
                        "name": user_node.get("username"),
                        "first_name": user_node.get("first_name"),
                        "last_name": user_node.get("last_name"),
                        "email": email,
                        "project": ConfigClass.TEST_PROJECT_CODE,
                        "status": "Pending Review",
                        "notes": notes,
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
        project_node = self.get_project_by_code(ConfigClass.TEST_PROJECT_CODE)

        # Add neo4j relation
        response = neo4j_client.create_relation(
            user_node["id"],
            project_node["id"],
            ConfigClass.TEST_PROJECT_ROLE,
            properties={"status": "active"}
        )
        if response.get("code") != 200:
            error_msg = 'Error getting container in neo4j' + str(response.get("result"))
            logger.error(error_msg)
            raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=str(error_msg))

    def post(self):
        res = APIResponse()
        data = request.get_json()
        email = data.get("email")
        username = data.get("username")
        logger.info(f"TestRequest called: {username}")
        email_service = SrvEmail()
        neo4j_client = Neo4jClient()
        if self.is_duplicate_user(username, email):
            return res.response, res.code

        ldap_client = LdapClient()
        ldap_client.connect(ConfigClass.TEST_PROJECT_CODE)
        user_dn, user_data = ldap_client.get_user_by_username(username)
        if not user_dn:
            # User not found, send alert to support
            logger.info(f"User not found in AD: {username}")
            email_service.send(
                subject="Request for VRE Test Account Denied - Invalid Username",
                receiver=ConfigClass.EMAIL_SUPPORT,
                sender=ConfigClass.EMAIL_SUPPORT,
                msg_type="html",
                template="test_account/support_notification.html",
                template_kwargs={
                    "title": "VRE test account request denied",
                    "username": username,
                    "email": email,
                    "project": ConfigClass.TEST_PROJECT_CODE,
                    "status": "Denied",
                    "notes": "Username does not exist in Active Directory",
                    "send_date": get_formatted_datetime("CET"),
                },
            )
            return res.response, res.code

        ldap_email = user_data.get("mail")[0].decode()
        first_name = user_data.get("givenName", "")[0].decode()
        if not first_name:
            first_name = username
        last_name = user_data.get("sn", "")[0].decode()

        if ldap_email == email:
            # User found in AD, create user and send email to user and support
            logger.info(f"User found in AD, email matches: {username}")
            self.add_user_to_ad_group(user_dn, "vre-users")
            self.add_user_to_ad_group(user_dn, ConfigClass.TEST_PROJECT_CODE)
            self.create_user(email)

            project_node = self.get_project_by_code(ConfigClass.TEST_PROJECT_CODE)
            email_service.send(
                subject="Auto-Notification: Request for VRE Test Account Approved",
                receiver=ConfigClass.EMAIL_SUPPORT,
                sender=ConfigClass.EMAIL_SUPPORT,
                msg_type="html",
                template="test_account/support_notification.html",
                template_kwargs={
                    "first_name": first_name,
                    "last_name": last_name,
                    "username": username,
                    "email": email,
                    "project_name": ConfigClass.TEST_PROJECT_CODE,
                    "title": "VRE test account request submitted and approved",
                    "status": "Approved",
                    "send_date": get_formatted_datetime("CET"),
                },
            )
            email_service.send(
                subject="Your request for a test account has been approved",
                receiver=email,
                sender=ConfigClass.EMAIL_SUPPORT,
                msg_type="html",
                template="test_account/user_created.html",
                template_kwargs={
                    "first_name": first_name,
                    "project_code": ConfigClass.TEST_PROJECT_CODE,
                    "project_role": ConfigClass.TEST_PROJECT_ROLE,
                    "project_name": project_node["name"],
                    "url": ConfigClass.VRE_DOMAIN + "/vre",
                    "url_guide": ConfigClass.VRE_DOMAIN + "/xwiki",
                    "support_email": ConfigClass.EMAIL_SUPPORT,
                },
            )
        else:
            # User found in AD but email doesn't match, send email to support
            logger.info(f"User found in AD, email doesn't match: {username}")
            email_service.send(
                subject="Action Required: Request for VRE Test Account submitted, review required",
                receiver=ConfigClass.EMAIL_SUPPORT,
                sender=ConfigClass.EMAIL_SUPPORT,
                msg_type="html",
                template="test_account/support_notification.html",
                template_kwargs={
                    "title": "VRE test account request pending review",
                    "name": f"{first_name} {last_name}",
                    "username": username,
                    "email": email,
                    "project": ConfigClass.TEST_PROJECT_CODE,
                    "status": "Pending Review",
                    "notes": "Email address does not match username in Active Directory",
                    "send_date": get_formatted_datetime("CET"),
                },
            )
        ldap_client.disconnect()
        return res.response, res.code


class ContractRequest(Resource):
    def post(self):
        res = APIResponse()
        data = request.get_json()
        agreement_info = data.get("contract_description")
        why_interested = data.get("interest_description")
        email = data.get("email")
        name = data.get("first_name") + " " + data.get("last_name")
        logger.info(f"ContractRequest called: {email}")

        email_service = SrvEmail()
        email_service.send(
            subject="Action Required: Pending Request for VRE Test Account",
            receiver=ConfigClass.EMAIL_SUPPORT,
            sender=ConfigClass.EMAIL_SUPPORT,
            msg_type="html",
            template="test_account/support_notification.html",
            template_kwargs={
                "title": "VRE test account request pending review",
                "name": name,
                "email": email,
                "project": ConfigClass.TEST_PROJECT_CODE,
                "status": "Pending Review",
                "agreement_info": agreement_info,
                "why_interested": why_interested,
                "send_date": get_formatted_datetime("CET"),
            },
        )
        email_service.send(
            subject="Your request for a test account is under review",
            receiver=email,
            sender=ConfigClass.EMAIL_SUPPORT,
            msg_type="html",
            template="test_account/contract_user_create.html",
            template_kwargs={
                "url_guide": ConfigClass.VRE_DOMAIN + "/xwiki",
                "support_email": ConfigClass.EMAIL_SUPPORT,
            },
        )
        return res.response, res.code
