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

# from app.routers import api_root
# from app.routers.v1 import api_data_download
# from app.routers.v2 import api_data_download as api_data_download_v2
# from app.routers.v2 import api_object_get as api_object_get

from users import ops_user, user_account_management, accounts, ops_admin
from users.permissions import permissions


def api_registry(app: FastAPI):
    # app.include_router(api_root.router)
    app.include_router(ops_user.router, prefix="/v1")
    app.include_router(user_account_management.router, prefix="/v1")
    app.include_router(permissions.router, prefix="/v1")
    app.include_router(accounts.router, prefix="/v1")
    app.include_router(ops_admin.router, prefix="/v1")
