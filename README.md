TravelBird
==========

Having fun with Django &amp; Postgres and getting a new awesome job

requirements.txt file contains all the necessary dependencies

Features
----------
* Bootstrap front-end and Django backend ( via `django_admin_bootstrapped` )
* Uses PostgreSQL db backend
* AJAX login & registration
* Django administration
* Haystack with ElasticSearch Backend
* Tastypie API to enable create & delete accounts
* Soft deletes through Django Admin UI. All the records are filtered out automatically.
* Talks with TravelBird API to send new records and deleted ones via Django Command
``` python manage.py synch_accounts```

* Search via API on ex: 
```http://localhost:8000/api/v1/account/search/?q=john@doe.com&format=json&username=travelbird&api_key=<api_key>```

Future implementation
--------------
* Better exception handling
* Implement search on front end

API via Tastypie 
----------------
if http is installed run the following shell command

```http POST http://localhost:8000/api/v1/account/\?format\=json\&username\=travelbird\&api_key\=<api_key> email=john@doe.com username=johndoer synched=False imported=True deleted=False password=1234 external_id=-4```

The following HTTP Response will be generated
```
HTTP/1.0 201 CREATED
Content-Type: application/json; charset=utf-8
Date: Sun, 18 Nov 2012 14:05:54 GMT
Location: http://localhost:8000/api/v1/account/72/
Server: WSGIServer/0.1 Python/2.7.3

{
    "deleted": "False", 
    "email": "john@doe.com", 
    "external_id": -4, 
    "id": "72", 
    "imported": true, 
    "name": "", 
    "password": "1234", 
    "resource_uri": "/api/v1/account/72/", 
    "synched": "False", 
    "username": "johndoer"
}
```