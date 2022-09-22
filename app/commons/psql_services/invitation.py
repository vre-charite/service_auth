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

from fastapi_sqlalchemy import db
from logger import LoggerFactory

from app.models.api_response import EAPIResponseCode
from app.models.sql_invitation import InvitationModel
from app.resources.error_handler import APIException

_logger = LoggerFactory('api_invitation').get_logger()


def query_invites(query: dict) -> list:
    try:
        invites = db.session.query(InvitationModel).filter_by(**query).all()
    except Exception as e:
        error_msg = f'Error querying invite in psql: {str(e)}'
        _logger.error(error_msg)
        raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=error_msg)
    return invites


def create_invite(model_data: dict) -> InvitationModel:
    try:
        invitation_entry = InvitationModel(**model_data)
        db.session.add(invitation_entry)
        db.session.commit()
        return invitation_entry
    except Exception as e:
        error_msg = f'Error creating invite in psql: {str(e)}'
        _logger.error(error_msg)
        raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=error_msg)
