# minty

**Beware: Don't put sensitive data like password in `config.py` or any file in this repo**

## A better way to setup

```
$ pip3 install virtualenv
$ python3 -m venv env
$ source env/bin/activate
$ ./env/bin/pip3 install -r requirements.txt
$ ./env/bin/python3 run.py
$ deactivate
```

*Could integrate with `smartcd`*


## Todo

- Replace sqlite with posgresql, mongodb (Flask-mongoengine) and redis (flask-redis)
- Change templates layout/error and security
- Remove Food, Restaurant
- Add first minty API to check `mintcast` postgresql data
	- using server 52.90.74.mask
	- **Wrap up CURD**
- **Wrap up DataCatalog-Query API (CURD in models.py)**
- Remove Oauth and users
- API
	- Using offset to query Data Catalog
	- According to Query from dc, store offset and run `mintcast`
		- handle single file (to generate tiles request)
		- handle timeseries (to generate tiles request)
		- handle diff (to generate tiles request)
		- handle trend (to generate chart request)
		- handle csv (to generate chart request)
	- Autocomplete-Redis Search API
	- MongoDB return dataset json
	- API handle requests from mint-ui.org
	- ? webhook to mint-ui.org


## Database config

database.py
```
# -*- coding: utf-8 -*-

MINTCAST_PATH = os.environ.get('MINTCAST_PATH')

class PostgresConfig(object):
	hostname = ''
	username = ''
	password = ''
	database = ''

class MongoConfig(object):
	hostname = ''
	username = ''
	password = ''
	database = ''

class RedisConfig(object):
	hostname = ''
	password = ''
```


## MVC Framework

Using MVC framework [Flask-MVC-Template](https://github.com/CharlyJazz/Flask-MVC-Template)

