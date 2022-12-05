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

import requests
from pytz import timezone

from config import ConfigSettings


def mask_email(email):
    sections = email.split("@")
    first = "".join(["*" for i in sections[0][0:-2]])
    second = "".join([i if i == "." else "*" for i in sections[1]])
    return sections[0][0] + first + sections[0][-1] + "@" + second


def get_formatted_datetime(tz):
    cet = timezone(tz)
    now = datetime.now(cet)
    return now.strftime("%Y-%m-%d, %-I:%M%p (%Z)")


def fetch_geid():
    entity_id_url = ConfigSettings.UTILITY_SERVICE + f"/v1/utility/id"
    response = requests.get(entity_id_url)
    if response.status_code != 200:
        raise Exception('Entity id fetch failed: ' + entity_id_url + ": " + str(response.text))
    geid = response.json()['result']
    return geid
