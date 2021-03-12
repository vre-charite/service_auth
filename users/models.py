from pydantic import BaseModel


class BaseResponse(BaseModel):
    code: int = 200
    error_msg: str = ""
    result: list = []
    page: int = 1
    total: int = 1
    num_of_pages: int = 1


class PostAuthRequest(BaseModel):
    username: str
    passsword: str
    realm: str


class PostAuthResponse(BaseResponse):
    result: str = 'success'
