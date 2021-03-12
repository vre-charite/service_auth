from models.service_meta_class import MetaService
from config import ConfigClass
import requests
import json


class SrvEmail(metaclass=MetaService):
    def send(self, subject, receiver: list = [], content="", msg_type="plain", sender=ConfigClass.EMAIL_DEFAULT_NOTIFIER, \
            template=None, template_kwargs={}):
        '''
        (str, str, str, str, str) -> dict   #**TypeContract**
        '''
        url = ConfigClass.EMAIL_SERVICE
        payload = {
            "subject": subject,
            "sender": sender,
            "receiver": receiver,
            "msg_type": msg_type,
        }
        if content:
            payload["message"] = content
        if template:
            payload["template"] = template
            payload["template_kwargs"] = template_kwargs
        res = requests.post(
            url=url,
            json=payload
        )
        return json.loads(res.text)
