from flask_via.routers.default import Pluggable


from .views import *

routes = [
	Pluggable('/minty/layer/<md5>', LayerJson, 'findLayerByVectorMD5'),
	Pluggable('/minty/layer/dc/<dcid>', DcidJson, 'findLayerByDataCatalogID'),
	Pluggable('/minty/metadata', MetadataJson, 'metadata'),
	Pluggable('/minty/autocomplete', AutocompleteJson, 'autocomplete'),
	Pluggable('/minty/layer_index', AutocompleteJson, 'layer_index'),
	Pluggable('/minty/visualize/<dataset_id>', VisualizeAction, 'visualize_action'),
	Pluggable('/minty/viz_type', VizType, 'viz_type'),
	Pluggable('/minty/chart/<dataset_id>', ChartData, 'chart_data'),
	Pluggable('/minty/tilestache/index.html', TileStacheIndex, 'tilestache_index'),
	Pluggable('/minty/tilestache/config', TileStacheConfig, 'tilestache_config'),
]