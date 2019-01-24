from flask_rq2 import RQ
import subprocess
import os
import zipfile
import tarfile
import requests
from .models import *


MINTCAST_PATH = os.environ.get('MINTCAST_PATH')

rq_instance = RQ()

RESUTL_TTL=-1 # '7d'

@rq_instance.job(func_or_queue='high', timeout='30m', result_ttl=RESUTL_TTL)
def rq_add_job(x, y, id):
	print(id)
	raise Exception("EF")
	import time
	time.sleep(10)
	return x+y

@rq_instance.job(func_or_queue='high', timeout='30m', result_ttl=RESUTL_TTL)
def rq_run_job(command):
    # pre = "cd ../../mintcast&&export MINTCAST_PATH=.&&./../mintcast/bin/mintcast.sh"
	# command = pre + command
	todir = "cd " + "{}".format( MINTCAST_PATH ) + "&&"
	pre = "./bin/mintcast.sh"
	command = todir + pre + command
	out=subprocess.call(command, shell = True)
	return out

@rq_instance.job(func_or_queue='normal', timeout='30m', result_ttl=RESUTL_TTL)
def rq_create_bash_job(DcInstance, **command_args):
	ret = DcInstance._buildBash(**command_args)

@rq_instance.job(func_or_queue='normal', timeout='30m', result_ttl=RESUTL_TTL)
def rq_download_job(resource, dataset_id, index, dir_path):
     # = '/tmp/' + dataset_id
    is_zip = False
    is_tar = False
    if resource['resource_metadata'].get('is_zip') is not None:
        if resource['resource_metadata']['is_zip'] == 'true':
            is_zip = True

    file = resource['resource_data_url'].split('/')
    file_name = file[len(file) - 1]
    file_path = dir_path + '/' + file_name

    if file_name.find('.tar') != -1:
        is_tar = True

    response = requests.get(resource['resource_data_url'])
    if response.status_code == 200:
    	with open(file_path, 'wb') as f:
            f.write(response.content)

    if is_zip:
        zip_ref = zipfile.ZipFile(file_path, 'r')
        zip_ref.extractall(dir_path)
        zip_ref.close()
        os.remove(file_path)
    elif is_tar:
        tar_ref = tarfile.open(file_path, 'r')
        tar_ref.extractall(dir_path)
        tar_ref.close()
        os.remove(file_path)
    
    print("download file %d" %(index+1))
    return 'download done'


@rq_instance.job(func_or_queue='low', timeout='30m', result_ttl=RESUTL_TTL)
def rq_excep_job():
	out = subprocess.call("python /Users/xuanyang/Downloads/rai.py", shell = True)
	return out
