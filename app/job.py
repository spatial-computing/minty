from flask_rq2 import RQ
import subprocess
import os
import zipfile
import tarfile
import requests
import json

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
RUN_MINTCAST_JOB_TIMEOUT = '8h'
NORMAL_JOB_TIMEOUT = '30m'
DOWNLOAD_JOB_TIMEOUT = '4h'
def queue_job_with_connection(job, connection, *args, **kwargs):
    if not connection:
        return job

    from rq import Queue
    rq_queue = Queue(
        name=job.helper.queue_name,
        connection=connection,
        is_async=True
        # job_class='flask_rq2.job.FlaskJob'
    )
    
    job = rq_queue.enqueue(
        job.helper.wrapped,
        args=args,
        timeout=job.helper.timeout,
        result_ttl=job.helper.result_ttl,
        ttl=job.helper.ttl,
        depends_on=job.helper._depends_on,
        at_front=job.helper._at_front,
        meta=job.helper._meta,
        description=job.helper._description
    )
    
    return job


# @rq_instance.job(func_or_queue='high', timeout='30m', result_ttl=RESUTL_TTL)
# def rq_add_job(x, y, id):
#     print(id)
#     raise Exception("EF")
#     import time
#     time.sleep(10)
#     return x+y

@rq_instance.job(func_or_queue='normal', timeout=RUN_MINTCAST_JOB_TIMEOUT, result_ttl=RESUTL_TTL)
def rq_run_command_job(command, bash_id, redis_url):
    # pre = "cd ../../mintcast&&export MINTCAST_PATH=.&&./../mintcast/bin/mintcast.sh"
    # command = pre + command
    pre = "/bin/bash ./bin/mintcast.sh"
    command = "cd %s && %s %s" % (MINTCAST_PATH, pre, command)
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = p.communicate()
    # update the real job id and update data
    # rq_connection = redis_url_or_rq_connection
    # if isinstance(redis_url_or_rq_connection, str):

    logs = {
        "output": str(out, 'utf8') if isinstance(out, bytes) else str(out),
        "error": str(err, 'utf8') if isinstance(err, bytes) else str(err)
    }

    rq_connection = Redis.from_url(redis_url)

    run_command_job_done = queue_job_with_connection(
        rq_run_command_done_job, 
        rq_connection, 
        bash_id, 
        get_current_job().id, 
        logs,
        redis_url)
    return json.dumps(logs)

@rq_instance.job(func_or_queue='high', timeout=NORMAL_JOB_TIMEOUT, result_ttl=RESUTL_TTL)    
def rq_run_command_done_job(bash_id, job_id, logs, redis_url):
    import time
    time.sleep(2)
    from app.bash import bash_helper
    rq_connection = Redis.from_url(redis_url)
    bash_helper.update_bash_status(bash_id, job_id, logs, rq_connection)

@rq_instance.job(func_or_queue='high', timeout=NORMAL_JOB_TIMEOUT, result_ttl=RESUTL_TTL)
def rq_create_bash_job(dc_instance, **command_args):
    ret = dc_instance._buildBash(**command_args)

@rq_instance.job(func_or_queue='high', timeout=NORMAL_JOB_TIMEOUT, result_ttl=parse_timeout(RESUTL_TTL))
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

            register_following_job_callback(redis_url)
            scheduler = Scheduler('high', connection=rq_connection) # Get a scheduler for the "foo" queue
            scheduler.cancel(get_current_job())
        else:
            raise Exception('One or more downloads failed')
    except Exception as e:
        print(e)
        import traceback
        traceback.print_tb(e.__traceback__)
        print("Canceling scheduler", get_current_job().id)
        scheduler = Scheduler('high', connection=rq_connection) # Get a scheduler for the "foo" queue
        scheduler.cancel(get_current_job())
        # get_current_job().cancel()
        # requests.post('http://127.0.0.1:65522/rq/cancel_scheduler',  data = json.dumps({job_id: get_current_job()}))

@rq_instance.job(func_or_queue='low', timeout=DOWNLOAD_JOB_TIMEOUT, result_ttl=RESUTL_TTL)
def rq_download_job(resource, dataset_id, index, dir_path):
     # = '/tmp/' + dataset_id
    is_zip = False
    is_tar = False
    file = None
    resource_data_url = None
    if isinstance(resource, str):
        resource_data_url = resource
    else:
        if resource['resource_metadata'].get('is_zip') is not None:
            if resource['resource_metadata']['is_zip'] == 'true':
                is_zip = True
        resource_data_url = resource['resource_data_url']
    
    file = resource_data_url.split('/')    
    file_name = file[-1]
    file_path = dir_path + '/' + file_name
    # print('$$$', file, file_name, file_path)
    if file_name.find('.tar') != -1:
        is_tar = True
    if file_name.endswith('.zip'):
        is_zip = True
    # print('#####', is_tar, is_zip, file_name)
    # response = requests.get(resource['resource_data_url'])
    logs = {}
    
    download_command = "wget -O %s %s" % (file_path, resource_data_url)
    p = subprocess.Popen(download_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = p.communicate()
        # update the real job id and update data
        # rq_connection = redis_url_or_rq_connection
        # if isinstance(redis_url_or_rq_connection, str):


    out_zip, err_zip = "", ""
    if is_zip:
        unzip_command = "unzip -o -U %s -d %s" % (file_path, dir_path)
        p2 = subprocess.Popen(unzip_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out_zip, err_zip = p2.communicate()
        # zip_ref = zipfile.ZipFile(file_path, 'r')
        # zip_ref.extractall(dir_path)
        # zip_ref.close()
        os.remove(file_path)
    elif is_tar:
        tar_ref = tarfile.open(file_path, 'r')
        tar_ref.extractall(dir_path)
        tar_ref.close()
        os.remove(file_path)
    
    logs = {
        "output": str(out, 'utf8') if isinstance(out, bytes) else str(out),
        "error": str(err, 'utf8') if isinstance(err, bytes) else str(err)
    }
    if err_zip or out_zip:
        logs['output'] += str(out_zip, 'utf8') if isinstance(out_zip, bytes) else str(out_zip)
        logs['error'] += str(err_zip, 'utf8') if isinstance(err_zip, bytes) else str(err_zip)
    print("download file %d" %(index+1))
    return json.dumps(logs)


