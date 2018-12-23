# minty

**Beware: Don't put sensitive data like password in `config.py` or any file in this repo**

## A better way to setup

```
$ pip3 install virtualenv
$ python3 -m env
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
- Add first minty API to check postgresql data
- Remove Oauth and users
- ...

## MVC Framework

Using MVC framework [Flask-MVC-Template](https://github.com/CharlyJazz/Flask-MVC-Template)

