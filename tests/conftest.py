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

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateSchema, CreateTable
from sqlalchemy_utils import create_database, database_exists
from testcontainers.postgres import PostgresContainer

from app import create_app
from app.config import ConfigSettings
from app.models.sql_invitation import Base, InvitationModel


@pytest.fixture(scope='session', autouse=True)
def db():
    with PostgresContainer('postgres:14.1') as postgres:
        postgres_uri = postgres.get_connection_url()
        if not database_exists(postgres_uri):
            create_database(postgres_uri)
        engine = create_engine(postgres_uri)
        CreateTable(InvitationModel.__table__).compile(dialect=postgresql.dialect())
        if not engine.dialect.has_schema(engine, ConfigSettings.RDS_SCHEMA_PREFIX + '_invitation'):
            engine.execute(CreateSchema(ConfigSettings.RDS_SCHEMA_PREFIX + '_invitation'))
        Base.metadata.create_all(bind=engine)
        yield postgres


@pytest.fixture
def test_client(db):
    ConfigSettings.RDS_DB_URI = db.get_connection_url()
    app = create_app()
    client = TestClient(app)
    return client
