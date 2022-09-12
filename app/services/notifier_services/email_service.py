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

import json

import httpx

from app.config import ConfigSettings
from app.models.service_meta_class import MetaService


class SrvEmail(metaclass=MetaService):
    def send(
        self,
        subject: str,
        receiver: str,
        sender: str,
        content: str = '',
        msg_type: str = 'plain',
        template: str = None,
        template_kwargs: dict = None,
        attachments: list = [],
    ) -> None:

        '''
        Summary:
            The api is used to request a emailing sending operation
            by input payload

        Parameter:
            - subject(string): The subject of email
            - receiver(string): The reciever email
            - sender(string): The sender email
            - content(string): default="", The email content
            - msg_type(string): default="plain", the message type for email
            - template(string): default=None, email service support some predefined template
            - template_kwargs(dict): default={}, the parameters for the template structure

        Return:
            200 updated
        '''

        if not template_kwargs:
            template_kwargs = {}

        url = ConfigSettings.EMAIL_SERVICE
        payload = {
            'subject': subject,
            'sender': sender,
            'receiver': [receiver],
            'msg_type': msg_type,
            'attachments': attachments,
        }
        if content:
            payload['message'] = content
        if template:
            payload['template'] = template
            payload['template_kwargs'] = template_kwargs
        res = httpx.post(url=url, json=payload)
        return json.loads(res.text)
