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

from enum import Enum
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field
from pydantic.types import constr


class UserGroupPOST(BaseModel):

    username: str
    groupname: str


class RealmRolesPOST(BaseModel):

    project_roles: list
    project_code: str


class UserInRolePOST(BaseModel):
    role_names: list 
    username: str=None
    email: str=None
    page: int=0
    page_size: int=10
    order_by: str=None
    order_type: str="asc"
    status: str="active"