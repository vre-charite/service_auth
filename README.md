This repo documents the service of user management. 
### How to start the service
```
sudo docker-compose up
```


### How to use the service
* login 
```
$ curl --header "Content-Type: application/json"   \
--request POST   \
--data '{"username":"testuser061501","password":"!", "realm":"testrealms"}'  \
http://127.0.0.1:5060/users/auth
{
    "result": {
        "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJrY3VRQjVCcDNTQlhRR0NpOVNCNDVjTGFnWnNRWVhkdi1OY3hQbzNJTU84In0.eyJleHAiOjE1OTM0NzQyNzAsImlhdCI6MTU5MzQ3MDY3MCwianRpIjoiYmMxMzNlNGMtNGQ2Ni00YjgxLTk4OWUtMTFkNmYzZTUyNDYzIiwiaXNzIjoiaHR0cDovLzEwLjMuOS4yNDE6ODA4MC9hdXRoL3JlYWxtcy90ZXN0cmVhbG1zIiwiYXVkIjoiYWNjb3VudCIsInN1YiI6IjI4NTI2ODY3LTAyY2MtNDlhZS1iNDA1LTE1NzA3ZmRiOGI0NSIsInR5cCI6IkJlYXJlciIsImF6cCI6ImtvbmciLCJzZXNzaW9uX3N0YXRlIjoiZDdmYWYxYTQtNzc1Ni00ZmY1LWJlMTYtMTliMWYxZDVhNGVmIiwiYWNyIjoiMSIsInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJvZmZsaW5lX2FjY2VzcyIsInVtYV9hdXRob3JpemF0aW9uIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwic2NvcGUiOiJwcm9maWxlIGVtYWlsIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsIm5hbWUiOiJ0ZXN0dXNlcjA2MTUwMSB0ZXN0dXNlcjA2MTUwMSIsInByZWZlcnJlZF91c2VybmFtZSI6InRlc3R1c2VyMDYxNTAxIiwiZ2l2ZW5fbmFtZSI6InRlc3R1c2VyMDYxNTAxIiwiZmFtaWx5X25hbWUiOiJ0ZXN0dXNlcjA2MTUwMSJ9.A0PI94CG_DksQfAWCYZMRNhzJ3N_gzpzlOUtnatVaq2HoLT5c3Y4sczZaFnXtOJpBB5KRTH1-RYZVhpPN_NWiyLUt_rwyWgk93AiKHWcCprdcz_PBCeYHPpgVaQuiadEMxTDrT1Cb8hB-E-QiH_bOMC-nWhQied7ZGWnR-fvEPZy08vv7dEr9xqtfkxYILg0SGccZKiBz7RmQBeOkU3W6ZBdkLGQvBL_anMrh-D1J2m_hebbDHZaoXKWIDVXlxF2CQ7Qk8FYCkHW2aSp5DWL97i2RdkyP7EnnrAC1IRCChnzylcHvnWOMIek51_iXi8KCXurlxhzk9MYVyVldjkZdQ",
        "expires_in": 3600,
        "refresh_expires_in": 1800,
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJjNTQ3ZTc1ZC01MWZjLTQwMDMtOGI3Yy1lYmJlMDFkODRmOTAifQ.eyJleHAiOjE1OTM0NzI0NzAsImlhdCI6MTU5MzQ3MDY3MCwianRpIjoiYWU5ZWEzMjItMDI4OS00NTliLWI2Y2MtN2I0ZTczMGVlNDk4IiwiaXNzIjoiaHR0cDovLzEwLjMuOS4yNDE6ODA4MC9hdXRoL3JlYWxtcy90ZXN0cmVhbG1zIiwiYXVkIjoiaHR0cDovLzEwLjMuOS4yNDE6ODA4MC9hdXRoL3JlYWxtcy90ZXN0cmVhbG1zIiwic3ViIjoiMjg1MjY4NjctMDJjYy00OWFlLWI0MDUtMTU3MDdmZGI4YjQ1IiwidHlwIjoiUmVmcmVzaCIsImF6cCI6ImtvbmciLCJzZXNzaW9uX3N0YXRlIjoiZDdmYWYxYTQtNzc1Ni00ZmY1LWJlMTYtMTliMWYxZDVhNGVmIiwic2NvcGUiOiJwcm9maWxlIGVtYWlsIn0.FJbpZBpdIfvAb0tuvGu1ToWIc4scKb0kK2t52AoB4Fw",
        "token_type": "bearer",
        "not-before-policy": 0,
        "session_state": "d7faf1a4-7756-4ff5-be16-19b1f1d5a4ef",
        "scope": "profile email"
    }
}
```


