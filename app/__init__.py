from flask import Flask, render_template, current_app
from flask_assets import Environment
from flask_wtf import CSRFProtect
from flask_security import Security, SQLAlchemyUserDatastore, utils
from flask_via import Via
# from flask_restful import Api
from flask_uploads import configure_uploads

from sqlalchemy_utils import database_exists, create_database
from sqlalchemy import create_engine

from .assets import create_assets
from .models import db
from .job import *

import rq_dashboard
# from .user.forms import SecurityRegisterForm
# from .admin import create_security_admin

from config import app_config

import os.path
# from flask_mongoengine import MongoEngine
# user_datastore = SQLAlchemyUserDatastore(db)

#flask.via.routers.restful  Resource not works.
from .bash.views import *


def create_app(config_name):
    # global user_datastore
    app = Flask(__name__)

    app.config.from_object(app_config[config_name])


    
    csrf = CSRFProtect()
    csrf.init_app(app)



    assets = Environment(app)
    create_assets(assets)

    # api = restful.Api(app)

    via = Via()
    # via.init_app(app, restful_api=api)
    via.init_app(app)


    # api = Api(app)
    # via.init_app(app, restful_api=api)
    # # add restful api for bash
    # api.add_resource(Bash, '/bash/<string:bash_id>')
    # api.add_resource(DeleteBash, '/bash/delete/<string:bash_id>')
    # api.add_resource(AddBash, '/bash/add')
    # api.add_resource(BashList, '/bashlist')
    # Code for desmostration the flask upload in several models - - - -

    # from .user import user_photo
    # from .restaurant import restaurant_photo
    # from .food import food_photo

    # configure_uploads(app, (restaurant_photo, food_photo, user_photo))

    # engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    # if not database_exists(engine.url):
    #     create_database(engine.url)

    # security = Security(app, user_datastore, register_form=SecurityRegisterForm)

    # create_security_admin(app=app, path=os.path.join(os.path.dirname(__file__)))
    # mongodb = MongoEngine()
    # mongodb.init_app(app)

    csrf.exempt(rq_dashboard.blueprint)
    #config rq
    rq.init_app(app)
    print(app.config['RQ_REDIS_URL'])
    app.config.from_object(rq_dashboard.default_settings)
    app.register_blueprint(rq_dashboard.blueprint, url_prefix="/rq")

    with app.app_context():
        db.init_app(app)
        db.create_all()
        # user_datastore.find_or_create_role(name='admin', description='Administrator')
        # db.session.commit()
        # user_datastore.find_or_create_role(name='end-user', description='End user')
        db.session.commit()

    @app.route('/', methods=['GET'])
    @app.route('/home', methods=['GET'])
    def index():
        # job = handlecsv.queue()
        return render_template('index.html')

    @app.errorhandler(403)
    def forbidden(error):
        return render_template('error/403.html', title='Forbidden'), 403

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('error/404.html', title='Page Not Found'), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        db.session.rollback()
        return render_template('error/500.html', title='Server Error'), 500

    return app