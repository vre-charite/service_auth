from flask_restx import Resource
from flask import request
import casbin
import casbin_sqlalchemy_adapter
from config import ConfigClass
from models.api_response import APIResponse, EAPIResponseCode
from module_keycloak.ops_admin import OperationsAdmin
from users import api
from services.logger_services.logger_factory_service import SrvLoggerFactory
from app import engine

_logger = SrvLoggerFactory('api_authorize').get_logger()


class Authorize(Resource):
    def get(self):
        api.logger.info('Calling CheckPermissions get')
        api_response = APIResponse()
        data = request.args
        project_role = data.get("role")
        project_zone = data.get("zone")
        resource = data.get("resource")
        operation = data.get("operation")
        if not project_role or not project_zone or not resource or not operation:
            _logger.info('Missing required paramter')
            api_response.set_error_msg("Missing required parameters")
            api_response.set_code(EAPIResponseCode.bad_request)
            return api_response.to_dict(), api_response.code

        api_response.set_result({"has_permission": False})
        try:
            adapter = casbin_sqlalchemy_adapter.Adapter(engine)
            enforcer = casbin.Enforcer("users/permissions/model.conf", adapter)
            if enforcer.enforce(project_role, project_zone, resource, operation):
                api_response.set_result({"has_permission": True})
                api_response.set_code(EAPIResponseCode.success)
                _logger.info(f'Access granted for {project_role}, {project_zone}, {resource}, {operation}')
        except Exception as e:
            error_msg = f"Error checking permissions - {str(e)}"
            _logger.error(error_msg)
            api_response.set_error_msg(error_msg)
            api_response.set_code(EAPIResponseCode.internal_error)
        return api_response.to_dict(), api_response.code
