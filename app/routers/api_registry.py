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

from fastapi import FastAPI

from app.routers import accounts, ops_admin, ops_user, user_account_management
from app.routers.invitation import invitation
from app.routers.permissions import permissions


def api_registry(app: FastAPI):
    # app.include_router(api_root.router)
    app.include_router(ops_user.router, prefix='/v1')
    app.include_router(user_account_management.router, prefix='/v1')
    app.include_router(permissions.router, prefix='/v1')
    app.include_router(accounts.router, prefix='/v1')
    app.include_router(ops_admin.router, prefix='/v1')
    app.include_router(invitation.router, prefix='/v1')
