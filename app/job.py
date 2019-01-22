#config rq
from flask_rq2 import RQ
import subprocess
from .models import *

import os
MINTCAST_PATH = os.environ.get('MINTCAST_PATH')

rq = RQ()



@rq.job
def add(x, y, id ):
	print(id)

	# bash=Bash.query.filter_by(id=id).first()
	# updatebash(id,bind="3")
	return x+y

@rq.job
def run(command):
	# pre="cd ../../mintcast&&export MINTCAST_PATH=.&&./../mintcast/bin/mintcast.sh"
	# command=pre+command
	todir="cd "+"{}".format(MINTCAST_PATH)+"&&"
	pre="./bin/mintcast.sh"
	command=todir+pre+command
	# out=subprocess.call(command,shell=True)
	return out
