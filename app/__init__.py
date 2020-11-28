from flask import Flask, request
from flask_cors import CORS
from config import ConfigClass
import importlib

import json
import requests

from flask_jwt import JWT,  JWTError
import jwt as pyjwt


def create_app(extra_config_settings={}):
    # initialize app and config app
    app = Flask(__name__, template_folder="../templates")
    app.config.from_object(__name__+'.ConfigClass')
    CORS(
        app, 
        origins="*",
        allow_headers=["Content-Type", "Authorization","Access-Control-Allow-Credentials"],
        supports_credentials=True, 
        intercept_exceptions=False)

    # dynamic add the dataset module by the config we set
    for apis in ConfigClass.api_modules:
        api = importlib.import_module(apis)
        api.module_api.init_app(app)
    return app
