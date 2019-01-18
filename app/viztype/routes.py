from flask_via.routers.default import Pluggable
from .views import *

routes = [
	Pluggable('/viztype', VizType, 'viz_type_index')
]