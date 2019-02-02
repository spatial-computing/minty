from flask_via.routers.default import Pluggable
from .views import *

routes = [
	Pluggable('/bash', BashList, 'bash_list'),
	Pluggable('/bash/delete/<string:bash_id>', DeleteBash, 'delete_bash'),
	Pluggable('/bash/add', AddBash, 'add_bash'),
	Pluggable('/bash/edit/<string:bash_id>', EditBash, 'edit_bash'),
	Pluggable('/bash/run', Run, 'run'),
	Pluggable('/bash/status', Status, 'status'),
	Pluggable('/bash/defaultsetting',MIntcastTaskDefaultSetting,'defaultsetting'),
	Pluggable('/bash/defaultsetting/controller',MIntcastTaskDefaultSettingController,'defaultsetting_controller'),
	Pluggable('/bash/cancel',Cancel,'cancel'),
	Pluggable('/bash/unregister', Unregister, 'unregister'),
	Pluggable('/bash/edit_dc_metadata', EditDcInfo, 'edit_dc_metadata'),
	Pluggable('/bash/register_dc_metadata', RegisterDcInfo, 'register_dc_metadata'),
]