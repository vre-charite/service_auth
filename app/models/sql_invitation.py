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

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

from app.config import ConfigSettings

Base = declarative_base()


class InvitationModel(Base):
    __tablename__ = 'invitation'
    __table_args__ = {'schema': ConfigSettings.RDS_SCHEMA_PREFIX + '_invitation'}
    id = Column(UUID(as_uuid=True), unique=True, primary_key=True, default=uuid4)
    invitation_code = Column(String())
    expiry_timestamp = Column(DateTime())
    create_timestamp = Column(DateTime(), default=datetime.utcnow)
    invited_by = Column(String())
    email = Column(String())
    platform_role = Column(String())
    project_role = Column(String())
    project_id = Column(String())
    status = Column(String())

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self):
        result = {}
        field_list = [
            'id',
            'invitation_code',
            'expiry_timestamp',
            'create_timestamp',
            'invited_by',
            'email',
            'platform_role',
            'project_role',
            'project_id',
            'status',
        ]
        for field in field_list:
            if getattr(self, field):
                result[field] = str(getattr(self, field))
            else:
                result[field] = ""
        return result
