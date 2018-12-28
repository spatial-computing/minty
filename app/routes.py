from flask_via.routers.default import Blueprint

routes = [
    Blueprint('minty', 'app.minty', template_folder='templates'),
]