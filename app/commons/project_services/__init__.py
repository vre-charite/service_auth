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

import httpx

from app.config import ConfigSettings
from app.models.api_response import EAPIResponseCode
from app.resources.error_handler import APIException


def get_project_by_geid(geid: str) -> dict:
    payload = {'global_entity_id': geid}
    response = httpx.post(ConfigSettings.NEO4J_SERVICE + 'nodes/Container/query', json=payload)
    if not response.json():
        raise APIException(status_code=EAPIResponseCode.not_found.value, error_msg=f'Project not found: {geid}')
    return response.json()[0]
