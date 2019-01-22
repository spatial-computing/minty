#config rq
from flask_rq2 import RQ
import subprocess
from .models import *
from .bash.bash_helper import updatebash

rq = RQ()



@rq.job
def add(x, y, id ):
	print(id)
	# updatebash(id,bind="3")
	return x+y

@rq.job
def run(command):
	pre="cd ../../mintcast&&export MINTCAST_PATH=.&&./../mintcast/bin/mintcast.sh"
	command=pre+command
	out=subprocess.call(command,shell=True)
	print(out)
	return out
