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

from functools import wraps
from models.api_response import APIResponse, EAPIResponseCode

class APIException(Exception):
    def __init__(self, status_code: int, error_msg: str):
        self.status_code = status_code
        self.content = {
            "code": self.status_code,
            "error_msg": error_msg,
            "result": "",
        }

def catch_internal(api_namespace):
    '''
    decorator to catch internal server error.
    '''
    def decorator(func):
        @wraps(func)
        async def inner(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as exce:
                if type(exce) == APIException:
                    raise exce
                respon = APIResponse()
                respon.code = EAPIResponseCode.internal_error
                respon.result = None
                err_msg = api_namespace + " " + str(exce)
                # _logger.error(traceback.format_exc())
                respon.error_msg = err_msg
                return respon.json_response()
        return inner
    return decorator