from flask_via.routers.default import Pluggable
from views import *

routes = [
	Pluggable('/minty/layer/<id>', LayerJson, 'layer'),
]