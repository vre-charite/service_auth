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

from pydantic import BaseModel, Field, validator

from app.models.api_response import EAPIResponseCode
from app.models.base_models import APIResponse
from app.resources.error_handler import APIException


class InvitationPUT(BaseModel):
    status: str = ""

    @validator('status')
    def validate_status(cls, v):
        if v not in ['complete', 'pending']:
            raise APIException(status_code=EAPIResponseCode.bad_request.value, error_msg='Invalid status')
        return v

class InvitationListPOST(BaseModel):
    page: int = 0
    page_size: int = 25
    order_by: str = 'create_timestamp'
    order_type: str = 'asc'
    filters: dict = {}


class InvitationPOST(BaseModel):
    email: str
    platform_role: str
    relationship: dict = {}
    invited_by: str

    @validator('relationship')
    def validate_relationship(cls, v):
        if not v:
            return v
        for key in ['project_geid', 'project_role', 'inviter']:
            if key not in v.keys():
                raise APIException(
                    status_code=EAPIResponseCode.bad_request.value,
                    error_msg=f'relationship missing required value {key}',
                )
        return v

    @validator('platform_role')
    def validate_platform_role(cls, v):
        if v not in ['admin', 'member']:
            raise APIException(status_code=EAPIResponseCode.bad_request.value, error_msg='Invalid platform_role')
        return v


class InvitationPOSTResponse(APIResponse):
    result: dict = Field(
        {},
        example={},
    )
