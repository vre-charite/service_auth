from models.service_meta_class import MetaService
from config import ConfigClass
import requests
import json


class SrvEmail(metaclass=MetaService):
    def send(self, subject, content, receiver: list = [], msg_type="plain", sender=ConfigClass.EMAIL_DEFAULT_NOTIFIER):
        '''
        (str, str, str, str, str) -> dict   #**TypeContract**
        '''
        url = ConfigClass.EMAIL_SERVICE
        payload = {
            "subject": subject,
            "sender": sender,
            "receiver": receiver,
            "message": content,
            "msg_type": msg_type
        }
        res = requests.post(
            url=url,
            json=payload
        )
        return json.loads(res.text)
