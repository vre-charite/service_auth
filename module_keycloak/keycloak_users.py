from config import ConfigClass
import requests


# This is archived
def create_user(create_user_url, username, first_name, last_name, email, password, access_token):
    # curl -v http://10.3.9.241:8080/auth/admin/realms/testrealms/users \
    # -H "Content-Type: application/json" -H "Authorization: bearer eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJrY3VRQjVCcDNTQlhRR0NpOVNCNDVjTGFnWnNRWVhkdi1OY3hQbzNJTU84In0.eyJleHAiOjE1OTI4NDQ5MDYsImlhdCI6MTU5Mjg0NDYwNiwianRpIjoiZDdlY2RhMTAtNTg4ZC00YjA5LWI1MzYtNTc0ZTA0OTAwNDlmIiwiaXNzIjoiaHR0cDovLzEwLjMuOS4yNDE6ODA4MC9hdXRoL3JlYWxtcy90ZXN0cmVhbG1zIiwiYXVkIjoicmVhbG0tbWFuYWdlbWVudCIsInN1YiI6IjMzMDlhMDE0LWFlYmMtNGJkMi1hNWEzLTRlNzNlNWMxNzk4ZSIsInR5cCI6IkJlYXJlciIsImF6cCI6ImFkbWluLWNsaSIsInNlc3Npb25fc3RhdGUiOiI3MTBiZmZlZS0yZjhkLTRkYTItYTI5MC1jNmNhNjBkNzlmNGMiLCJhY3IiOiIxIiwicmVhbG1fYWNjZXNzIjp7InJvbGVzIjpbImFkbWluLXJvbGUiLCJvZmZsaW5lX2FjY2VzcyIsInVtYV9hdXRob3JpemF0aW9uIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsicmVhbG0tbWFuYWdlbWVudCI6eyJyb2xlcyI6WyJ2aWV3LXJlYWxtIiwidmlldy1pZGVudGl0eS1wcm92aWRlcnMiLCJtYW5hZ2UtaWRlbnRpdHktcHJvdmlkZXJzIiwiaW1wZXJzb25hdGlvbiIsInJlYWxtLWFkbWluIiwiY3JlYXRlLWNsaWVudCIsIm1hbmFnZS11c2VycyIsInF1ZXJ5LXJlYWxtcyIsInZpZXctYXV0aG9yaXphdGlvbiIsInF1ZXJ5LWNsaWVudHMiLCJxdWVyeS11c2VycyIsIm1hbmFnZS1ldmVudHMiLCJtYW5hZ2UtcmVhbG0iLCJ2aWV3LWV2ZW50cyIsInZpZXctdXNlcnMiLCJ2aWV3LWNsaWVudHMiLCJtYW5hZ2UtYXV0aG9yaXphdGlvbiIsIm1hbmFnZS1jbGllbnRzIiwicXVlcnktZ3JvdXBzIl19fSwic2NvcGUiOiJwcm9maWxlIGVtYWlsIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsIm5hbWUiOiJBZG1pbmlzdHJhdG9yIEFkbWluaXN0cmF0b3IiLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJhZG1pbiIsImdpdmVuX25hbWUiOiJBZG1pbmlzdHJhdG9yIiwiZmFtaWx5X25hbWUiOiJBZG1pbmlzdHJhdG9yIn0.DayTLAcL6Bz3XxtYTGWVZlAVom9wtFrNp3dgLgFVUk2id7y8OeO7Y9Bv2vlfrXmGtC1KeV6sMW7V7zvu2LX5XHS_aY9OQeHLpcL5YWhT1CnDeK2m4JpSooIVglkj7t505rSw1Oz7FGReu2SefIagfKcc4_77pDq3El1-3oijfd-8UsvuQ6snK_lYaDX2AzR6-NyAq8cYob4z7veMmes5oSYHiLqkJzFedR2BzMvTXqALYKHiBeyzJ8ZlCataifqvwZXnNNu0g3ljUneohppS6k45iz4YOU5rDatECk5FkOt1-JpSy1hpXuIPn07M6_5EbpixQ3thCJCyDloPf9CsPw" \
    # --data '{ "username":"fortest06222", "firstName":"xyz","lastName":"xyz", "email":"demo6@gmail.com", "enabled":"true", "credentials":{"type":"password","value":"newPas1*","temporary":false}}'
    data = {
        'username': username, 
        'firstName': first_name, 
        'lastName':last_name, 
        'email':email, 
        'enabled':True,
        "credentials":{"type":"password","value":password,"temporary":False},
    }
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain', "Authorization": "bearer "+access_token}
    r = requests.post(create_user_url, data=json.dumps(data), headers=headers).json()
    print(r)
    return r

def login(client_id, client_secret, username, password, grant_type, login_url):
    # curl -d "client_id=kong" -d "client_secret=8215813e-7d5d-49a5-8601-a9ce46807221" \
    # -d "username=testuser061501" -d "password=Trillian42!" -d "grant_type=password" \
    # "http://10.3.9.241:8080/auth/realms/testrealms/protocol/openid-connect/token"
    payload = {
        'client_id': client_id, #ConfigClass.KEYCLOAK_CLIENT_ID, 
        'client_secret': client_secret, #ConfigClass.KEYCLOAK_SECRET, 
        'username':username, 
        'password':password, 
        "grant_type":grant_type, #ConfigClass.KEYCLOAK_GRANT_TYPE
    }
    r = requests.post(
        login_url, #ConfigClass.KEYCLOAK_BASE_URL, 
        data=payload
    )
    r = r.json()
    print(r)
    return r


def list_users(token, url):
#     curl \
#   -H "Authorization: bearer eyJhbGciOiJSUzI...." \
#   "http://localhost:8080/auth/admin/realms/master/users"
    headers = {"Authorization": "Bearer "+token}

    r = requests.get(
        url, #ConfigClass.KEYCLOAK_BASE_URL, 
        headers = headers
    ).json()

    return r

def query_users(token, url, param):
#     curl \
#   -H "Authorization: bearer eyJhbGciOiJSUzI...." \
#   "http://localhost:8080/auth/admin/realms/master/users?email=****"
    try:
        headers = {"Authorization": "Bearer "+token}
        r = requests.get(
            url,
            headers = headers,
            params=param
        ).json()
    except requests.exceptions.RequestException as e:
        return {'result': f'unable to query users {e}'}, 400
    return r