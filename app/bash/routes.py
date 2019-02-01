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
	Pluggable('/bash/cancel',Cancel,'cancel')
]