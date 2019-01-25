import os
import json

from app.models import Bash, db
from app.job import rq_run_command_job, rq_instance

MINTCAST_PATH = os.environ.get('MINTCAST_PATH')
COLUMN_NAME_DATA_FILE_PATH = 'data_file_path'
COLUMN_NAME_VIZ_TYPE = 'viz_type'

IGNORED_KEY_AS_PARAMETER_IN_COMMAND = {
    'id', 
    'viz_config', 
    'status', 
    'rqids', 
    '_sa_instance_state', 
    'file_type',
    'dev_mode_off',
    'command',
    'logs',
    COLUMN_NAME_DATA_FILE_PATH,
    COLUMN_NAME_VIZ_TYPE
}
MINTCAST_PATH_NEEDED_IN_COMMAND = {
    'with_shape_file',
    'load_colormap'
}
VIZ_TYPE_OF_TIMESERISE = {
    'mint-map-time-series'
}
VIZ_TYPE_OF_SINGLE_FILE = {
    'mint-map',
    'mint-chart'
}


def combine( args ):
    res = " "
    for key in args:
        if( key not in IGNORED_KEY_AS_PARAMETER_IN_COMMAND and args[key] not in {'', None, False}):
            param = key.replace("_", "-")

            if( args[key] == True ):
                res += "--%s " % (param)
            else:
                if key in MINTCAST_PATH_NEEDED_IN_COMMAND:
                    res += "--%s %s%s " % (param, MINTCAST_PATH.strip().rstrip('/') + '/', args[key])
                else:
                    res += "--%s '%s' " % (param, args[key])
    # if args[COLUMN_NAME_VIZ_TYPE] in VIZ_TYPE_OF_TIMESERISE:
    res += args[COLUMN_NAME_DATA_FILE_PATH] or '/tmp/tmp.tiff'
    return res

#find one by id 
def find_command_by_id(id, db_session=db.session):
    bash = db_session.query(Bash).filter_by(id = id).first()
    if bash is None:
        return "no bash"
    # if bash.command != '':
    #   return bash.command
    return combine(vars(bash))

def find_bash_by_id(id):
    bash = Bash.query.filter_by(id = id).first()
    return bash


#find all
def find_all():
    bashes = Bash.query.order_by("id desc").all()
    # res=[]
    # for bash in bashes:
    #    res.append(combine(vars(bash)))
    return bashes

# argument is a dic
def add_bash(db_session=db.session, **kwargs):
    newbash = Bash(**kwargs)
    newbash.command = combine(vars(newbash))
    db_session.add(newbash)
    db_session.commit()
    #print (bash)
    return newbash

#delete this bash
def delete_bash(id, db_session=db.session):
    bash = db_session.query(Bash).filter_by(id = id).first()
    db_session.delete(bash)
    db_session.commit()

#update bash
def update_bash(id, db_session=db.session, **kwargs):
    bash = db_session.query(Bash).filter_by(id = id).first()
    for key in kwargs:
        setattr(bash, key, kwargs[key])
    bash.command = combine(vars(bash))
    db_session.commit()
    return bash


def find_bash_attr(id, attr,db_session=db.session):
    bash = db_session.query(Bash).filter_by(id = id).first()
    bash = vars(bash)
    value = bash[attr] 
    return value


def add_job_id_to_bash_db(bashid, jobid, db_session=db.session, command=None):
    bash = db_session.query(Bash).filter_by(id = bashid).first()
    setattr(bash, "rqids", jobid)
    if command:
        setattr(bash, 'command', command)
    db_session.commit()

def run_bash(bash_id):
    command = find_command_by_id(bash_id)
    job = rq_run_command_job.queue(command, bash_id, rq_instance.redis_url)
    # job = excep.queue()
    #job = add.queue(1, 2, bashid)
    add_job_id_to_bash_db(bash_id, job.id, command=command)

def update_bash_status(bash_id, job_id, logs, rq_connection):
    from app.models import get_db_session_instance
    from rq.job import Job
    
    import requests
    API_UPDATE_VIZSTATUS_TO_DC = 'http://api.mint-data-catalog.org/datasets/update_dataset_viz_status'

    def update_viz_status_to_dc(dataset_id, viz_config):
        payload = {'dataset_id': dataset_id, 'viz_config_id': viz_config}
        req = requests.post(API_UPDATE_VIZSTATUS_TO_DC, data = json.dumps(payload))
        if req.status_code != 200:
            return 'error'
        
        response = req.json()
        #print(response)
        if not isinstance(response, dict):
            return 'error'

        if 'error' in response:
            print(response['error'])
            return 'error'

        return 'success'

    db_session = get_db_session_instance()
    bash = db_session.query(Bash).filter_by(id = bash_id).first()
    update_to_dc = ''
    if update_viz_status_to_dc(bash.md5vector, bash.viz_config) == 'success':
        update_to_dc = 'Update viz status to data catalog success.\nDataset_id: %s\nViz_config: %s' % (bash.md5vector, bash.viz_config)
    else:
        update_to_dc = 'Error in updating viz status to data catalog.\nDataset_id: %s\nViz_config: %s' % (bash.md5vector, bash.viz_config)
    
        
    _j = Job.fetch(job_id, connection=rq_connection)
    
    if _j.exc_info:
        logs['exc_info'] = str(_j.exc_info) + '\n\n' + update_to_dc
    else:
        logs['exc_info'] = update_to_dc

    bash.rqids = job_id
    bash.status = _j.get_status()
    bash.logs = json.dumps(logs)

    db_session.commit()
    return bash

def find_one(db_session=db.session):
    return db_session.query(Bash).first()

