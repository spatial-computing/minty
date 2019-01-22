#config rq
from flask_rq2 import RQ
import subprocess
import os
import urllib
import zipfile
from .models import *
from .bash.bash_helper import *
import os
MINTCAST_PATH = os.environ.get('MINTCAST_PATH')

rq = RQ()



@rq.job
def add(x, y, id ):
	print(id)
	command=findcommand_by_id(id)
	print(command)
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
	return command

@rq.job(timeout=1800)
def download(resource, dataset_id, index):
    dir_path = '/tmp/' + dataset_id
    is_zip = False
    if resource['resource_metadata'].get('is_zip') is not None:
        if resource['resource_metadata']['is_zip'] == 'true':
            is_zip = True

    file = resource['resource_data_url'].split('/')
    file_name = file[len(file) - 1]
    file_path = dir_path + '/' + file_name
    if is_zip:
        (name, header) = urllib.request.urlretrieve(resource['resource_data_url'], file_path)
        zip_ref = zipfile.ZipFile(file_path, 'r')
        zip_ref.extractall(dir_path)
        zip_ref.close()
        os.remove(file_path)
    else:
        (name, header) = urllib.request.urlretrieve(resource['resource_data_url'], file_path)
            
    print("download file %d" %(index+1))
    
    return 'done'
