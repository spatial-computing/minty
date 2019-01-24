from flask_rq2 import RQ
import subprocess
import os
import zipfile
import tarfile
import requests
from .models import *
from rq import get_current_job
from rq.utils import parse_timeout

from rq.job import Job
from rq.exceptions import NoSuchJobError
from redis import Redis
from rq_scheduler import Scheduler

MINTCAST_PATH = os.environ.get('MINTCAST_PATH')

def job_fetch(self, id):
    job = False, None
    try:
        job = True, Job.fetch(id, connection=rq_instance.connection)
    except NoSuchJobError as e:
        job = False, str(e)
    except Exception as e:
        job = False, str(e)
    return job

# class method injection
RQ.job_fetch = job_fetch

rq_instance = RQ()

RESUTL_TTL = '7d' # -1 for never expire, clean up result key manually


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
    out = subprocess.call(command, shell = True)
    return out

@rq_instance.job(func_or_queue='normal', timeout='30m', result_ttl=RESUTL_TTL)
def rq_create_bash_job(dc_instance, **command_args):
    ret = dc_instance._buildBash(**command_args)

@rq_instance.job(func_or_queue='high', timeout='30m', result_ttl=parse_timeout(RESUTL_TTL))
def rq_check_job_status_scheduler(job_ids, register_following_job_callback, redis_url):
    jobs = []
    status = True
    rq_connection = Redis.from_url(redis_url)
    try:
        for jid in job_ids:
                _j = Job.fetch(jid, connection=rq_connection)
                jobs.append(_j)
                print('Checking job', _j.id)
    except NoSuchJobError as e:
        status = False
    except Exception as e:
        status = False

    print(jobs)
    try:
        if status:
            for job in jobs:
                if job.status != 'finished':
                    print('not finished yet')
                    return 

            register_following_job_callback(rq_connection)

        else:
            raise Exception('One or more downloads failed')
    except Exception as e:
        print(e)
        import traceback
        traceback.print_tb(e.__traceback__)
        print("Canceling scheduler", get_current_job().id)
        scheduler = Scheduler('high', connection=Redis.from_url(redis_url)) # Get a scheduler for the "foo" queue
        scheduler.cancel(get_current_job())
        # get_current_job().cancel()
        # requests.post('http://127.0.0.1:65522/rq/cancel_scheduler',  data = json.dumps({job_id: get_current_job()}))

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
