from flask_via.routers.default import Pluggable


from .views import *

routes = [
	Pluggable('/minty/layer/<md5>', LayerJson, 'layer'),
	Pluggable('/minty/metadata', MetadataJson, 'metadata'),
	Pluggable('/minty/autocomplete', AutocompleteJson, 'autocomplete')
]