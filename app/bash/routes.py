from flask_via.routers.default import Pluggable
from .views import *

routes = [
	Pluggable('/bash', BashList, 'bash_list'),
	Pluggable('/bash/delete/<string:bash_id>', DeleteBash, 'delete_bash'),
	Pluggable('/bash/add', AddBash, 'add_bash'),
	Pluggable('/bash/view/<string:bash_id>', Bash, 'view_bash'),
	Pluggable('/bash/run', Run, 'run'),
]