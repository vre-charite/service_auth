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

from fastapi import APIRouter
from fastapi_utils import cbv

import casbin
import casbin_sqlalchemy_adapter
from common.services.logger_services.logger_factory_service import SrvLoggerFactory
# from flask import request
# from flask_restx import Resource
from sqlalchemy import create_engine

from config import ConfigSettings
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
# from users import api

from resources.error_handler import catch_internal


_engine = None

router = APIRouter()

_API_TAG = '/v1/authorize'
_API_NAMESPACE = "api_authorize"
_logger = SrvLoggerFactory(_API_NAMESPACE).get_logger()


def _get_sqlalchemy_engine():
    """Get or create engine for sqlalchemy."""

    global _engine

    if _engine is None:
        _engine = create_engine(ConfigSettings.RDS_DB_URI, max_overflow=10, pool_recycle=1800, pool_size=10)

    return _engine


@cbv.cbv(router)
class Authorize:

    def __init__(self):
        pass

    @router.get("/authorize", tags=[_API_TAG],
                 summary='check the authorization for the user')
    @catch_internal(_API_NAMESPACE)
    async def get(self, role: str, zone: str, resource: str, operation: str):
        # api.logger.info('Calling CheckPermissions get')
        api_response = APIResponse()

        project_role = role
        project_zone = zone
        # if not project_role or not project_zone or not resource or not operation:
        #     _logger.info('Missing required paramter')
        #     api_response.set_error_msg("Missing required parameters")
        #     api_response.set_code(EAPIResponseCode.bad_request)
        #     return api_response.to_dict(), api_response.code

        api_response.result = {"has_permission": False}
        try:
            adapter = casbin_sqlalchemy_adapter.Adapter(_get_sqlalchemy_engine())
            enforcer = casbin.Enforcer("users/permissions/model.conf", adapter)
            if enforcer.enforce(project_role, project_zone, resource, operation):
                api_response.result = {"has_permission": True}
                api_response.code = EAPIResponseCode.success
                _logger.info(f'Access granted for {project_role}, {project_zone}, {resource}, {operation}')

        except Exception as e:
            error_msg = f"Error checking permissions - {str(e)}"
            _logger.error(error_msg)
            api_response.error_msg = error_msg
            api_response.code = EAPIResponseCode.internal_error

        return api_response.json_response()
