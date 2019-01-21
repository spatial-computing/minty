from flask_via.routers.default import Pluggable
from .views import *

routes = [
	Pluggable('/viztype', VizType, 'viztype_index')
]