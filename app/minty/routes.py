from flask_via.routers.default import Pluggable


from .views import *

routes = [
	Pluggable('/minty/layer/<md5>', LayerJson, 'findLayerByVectorMD5'),
	Pluggable('/minty/layer/dc/<dcid>', DcidJson, 'findLayerByDataCatalogID'),
	Pluggable('/minty/metadata', MetadataJson, 'metadata'),
	Pluggable('/minty/autocomplete', AutocompleteJson, 'autocomplete'),
	Pluggable('/minty/layer_index', AutocompleteJson, 'layer_index')
]