import os
import random, string
from database import MongoConfig, PostgresConfig
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class DevelopmentConfig(object):
    # Flask

    SECRET_KEY = 'SECRET_KEY'
    TEMPLATES_AUTO_RELOAD = True
    DEBUG = True
    SEND_FILE_MAX_AGE_DEFAULT = 0
    
    #Flask-Assets

    ASSETS_DEBUG = False

    # Flask-Via

    VIA_ROUTES_MODULE = "app.routes"

    #Flask-Security

    SECURITY_REGISTERABLE = True
    SECURITY_TRACKABLE = True
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_LOGIN_URL = '/login/'
    SECURITY_LOGOUT_URL = '/logout/'
    SECURITY_REGISTER_URL = '/register/'
    SECURITY_POST_LOGIN_VIEW = "/"
    SECURITY_POST_LOGOUT_VIEW = "/"
    SECURITY_POST_REGISTER_VIEW = "/"
    SECURITY_LOGIN_USER_TEMPLATE = 'security/login.html'
    SECURITY_REGISTER_USER_TEMPLATE = 'security/register.html'

    #Flask-SQLAlchemy

    #SQLALCHEMY_DATABASE_URI = 'sqlite:///{}'.format(os.path.join(BASE_DIR, 'app.db'))
    DATABASE_URL = PostgresConfig.POSTGRES_CONNECTION
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    MONGODB_DATABASE_URI = MongoConfig.MONGODB_CONNECTION

    #Flask-Script

    APP_FOLDER = "app/"
    
    #OAUTH LOGIN

    OAUTH_CREDENTIALS = {
        'facebook': {
            'id': '638111216387395',
            'secret': 'c374a53decb75c2043ccd0e4a0eb8c28'
        },
        'twitter': {
            'id': 't6nK168ytZ7w7Rj4uJD3bXi5L',
            'secret': 'L537M7QT810Qe0zMCB1od3bKe6ljx2nyDkxxF49gaHtSJrmHA1'
        },
        'google': {
            'id': '1080912678595-adm52eo5f78jru65923qia22itfasa7d.apps.googleusercontent.com',
            'secret': '1vq9zxw2rMiBtUVeLlAlNOVw'
        }
    }

class TestingConfig(DevelopmentConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///{}'.format(os.path.join(BASE_DIR, 'testing.db'))

app_config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig
}