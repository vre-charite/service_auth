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

import requests

from config import ConfigSettings


def catch_internal(func):
    '''
    decorator to catch internal server error.
    '''

    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return {
                "error_msg": str(e),
                "result": "",
                "code": 500,
            }

    return inner


class Neo4jClient(object):

    def __init__(self):
        self.result = {
            "result": None,
            "error_msg": "",
            "code": 200,
        }

    # Shared
    @catch_internal
    def node_create(self, label, data):
        response = requests.post(
            ConfigSettings.NEO4J_SERVICE + f"nodes/{label}", json=data)
        result = self.result.copy()
        result["result"] = response.json()
        return result

    @catch_internal
    def node_query(self, label, data):
        response = requests.post(
            ConfigSettings.NEO4J_SERVICE + f"nodes/{label}/query", json=data)
        result = self.result.copy()
        result["result"] = response.json()
        return result

    @catch_internal
    def get_relation(self, start_id, end_id):
        relation_query = {"start_id": start_id, "end_id": end_id}
        response = requests.get(
            ConfigSettings.NEO4J_SERVICE + f"relations", params=relation_query)
        result = self.result.copy()
        result["result"] = response.json()
        return result

    @catch_internal
    def create_relation(self, start_id, end_id, label, properties={}):
        payload = {"start_id": start_id, "end_id": end_id}
        if properties:
            payload['properties'] = properties
        response = requests.post(
            ConfigSettings.NEO4J_SERVICE + f"relations/{label}", json=payload)
        result = self.result.copy()
        result["result"] = response.json()
        return result

    @catch_internal
    def update_node(self, label, node_id, data):
        response = requests.put(
            ConfigSettings.NEO4J_SERVICE + f"nodes/{label}/node/{node_id}", json=data)
        result = self.result.copy()
        result["result"] = response.json()
        return result

    @catch_internal
    def update_relation(self, start_id, end_id, label, properties={}):
        payload = {"start_id": start_id, "end_id": end_id, "new_label": label}
        if properties:
            payload['properties'] = properties
        response = requests.put(
            ConfigSettings.NEO4J_SERVICE + f"relations/{label}", json=payload)
        result = self.result.copy()
        result["result"] = response.json()
        return result

    # Datasets

    def get_container_by_geid(self, geid):
        response = self.node_query("Container", {"global_entity_id": geid})
        if not response.get("result"):
            if not response.get("error_msg"):
                self.result["error_msg"] = "Container not found"
                self.result["code"] = 404
            return self.result
        dataset_node = response["result"][0]
        self.result["result"] = response["result"][0]
        return self.result

    def get_container_by_code(self, code):
        response = self.node_query("Container", {"code": code})
        if not response.get("result"):
            if not response.get("error_msg"):
                response["error_msg"] = "Container not found"
                response["code"] = 404
            return response
        dataset_node = response["result"][0]
        response["result"] = dataset_node
        return response

    def get_container_role(self, dataset_geid, user_id):
        response = self.get_container_by_geid(dataset_geid)
        if response.get("error_msg"):
            return response
        dataset_node = response["result"]
        relation = self.get_relation(user_id, dataset_node["id"])
        if not relation["result"]:
            self.result["error_msg"] = "Role not found"
            self.result["code"] = 404
            return self.result
        self.result["result"] = relation["result"][0]['r']['type']
        return self.result

    def get_container_from_folder(self, geid):
        response = self.node_query("Folder", {"global_entity_id": geid})
        if not response.get("result"):
            if not response.get("error_msg"):
                self.result["error_msg"] = "Folder not found"
                self.result["code"] = 404
            return self.result
        folder_node = response["result"][0]

        response = self.node_query(
            "Container", {"code": folder_node["project_code"]})
        if not response.get("result"):
            if not response.get("error_msg"):
                self.result["error_msg"] = "Container not found"
                self.result["code"] = 404
            return self.result
        self.result["result"] = response["result"][0]
        return self.result

    # Users
    def get_user_by_email(self, email):
        response = self.node_query("User", {"email": email})
        if not response.get("result"):
            if not response.get("error_msg"):
                response["error_msg"] = "User not found"
                response["code"] = 404
            return response
        response["result"] = response["result"][0]
        return response

    def create_user(self, user_data):
        response = self.node_create("User", user_data)
        response["result"] = response["result"][0]
        return response

    def update_user(self, node_id, user_data):
        if "time_lastmodified" in user_data:
            # auto managed by neo4j, otherwise will throws the error
            del user_data['time_lastmodified']
        response = self.update_node("User", node_id, user_data)
        response["result"] = response["result"]
        return response

    def get_user_linked_projects(self, user_id):
        url = ConfigSettings.NEO4J_SERVICE + "relations/query"
        payload = {
            "start_label": "User",
            "end_label": "Container",
            "start_params": {"id": user_id}
        }
        response = requests.post(
            url=url,
            json=payload
        )
        return response

    def get_user_by_geid(self, geid):
        response = self.node_query("User", {"global_entity_id": str(geid)})
        if not response.get("result"):
            if not response.get("error_msg"):
                response["error_msg"] = "User not found"
                response["code"] = 404
            return response
        response["result"] = response["result"][0]
        return response
