#config rq
from flask_rq2 import RQ
import subprocess
rq = RQ()



@rq.job
def add(x, y):
    return x + y

@rq.job
def run(command):
	pre="cd ../../mintcast&&export MINTCAST_PATH=.&&./../mintcast/bin/mintcast.sh"
	command=pre+command
	out=subprocess.call(command,shell=True)
	return out
