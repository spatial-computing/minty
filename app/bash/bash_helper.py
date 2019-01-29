import os
import subprocess
from database import MongoConfig
import pymongo
import json
from app.models import Bash, db
from app.job import rq_run_command_job, rq_instance 
from sqlalchemy.orm import load_only

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
    'command',
    'logs',
    'dataset_id',
    'data_url',
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
PROJECTION_OF_BASH_NEED_TO_DISPLAY_ON_WEB = [
        Bash.id, 
        Bash.command, 
        Bash.rqids, 
        Bash.dev_mode_off, 
        Bash.scp_to_default_server, 
        Bash.disable_new_res, 
        Bash.viz_config, 
        Bash.viz_type,
        Bash.file_type,
        Bash.md5vector
]

PROJECTION_OF_BASH_USER_COULD_MODIFY = [
    Bash.id,
    Bash.type,
    Bash.qml,
    Bash.dir,
    Bash.md5vector,
    Bash.output_dir_structure,
    Bash.start_time,
    Bash.end_time,
    Bash.datatime_format,
    Bash.layer_name,
    Bash.output,
    Bash.bounds,
    Bash.first_file,
    Bash.time_stamp,
    Bash.time_steps,
    Bash.time_format,
    Bash.with_shape_file,
    Bash.dev_mode_off,
    Bash.scp_to_default_server,
    Bash.tiled_ext,
    Bash.disable_clip,
    Bash.disable_new_res,
    Bash.force_proj_first,
    Bash.with_south_sudan_shp,
    Bash.command,
    Bash.data_file_path,
    Bash.chart_type,
    Bash.load_colormap,
    Bash.file_type,
    Bash.directory_structure,
    Bash.netcdf_subdataset,
    Bash.viz_type,
    Bash.data_url
]
def combine( args ):

    mongo_client = pymongo.MongoClient(MongoConfig.MONGODB_CONNECTION)
    mongo_db = mongo_client["mintcast"]
    mongo_mintcast_default = mongo_db["metadata"]
    default_setting = mongo_mintcast_default.find_one({'type': 'minty-mintcast-task-dashboard-default-value-setting'}, {"_id": False, "type":False})
    if (default_setting['use_default_setting'] == 'true'):
        for key in default_setting:
            if key != 'use_default_setting':
                args[key] = True if default_setting[key] == 'true' else False 
    res = " "
    # if == True
    # args[key] = default
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
    if args[COLUMN_NAME_VIZ_TYPE] not in VIZ_TYPE_OF_TIMESERISE:
        # res += "/tmp/tmp.tif" # for test
        res += args[COLUMN_NAME_DATA_FILE_PATH]
    return res

#find one by id 
def find_command_by_id(id, db_session=db.session):
    bash = db_session.query(Bash)\
                     .with_entities(*PROJECTION_OF_BASH_USER_COULD_MODIFY)\
                     .filter_by(id = id).first()
    if bash is None:
        return "no bash"
    # if bash.command != '':
    #   return bash.command
    return combine(bash._asdict())

def find_bash_by_id(id, db_session=db.session):
    bash = db_session.query(Bash)\
                     .with_entities(*PROJECTION_OF_BASH_USER_COULD_MODIFY)\
                     .filter_by(id = id).first()
    return bash


#find all
def find_all(limit = 20, page=0, db_session=db.session):
    bashes = db_session.query(Bash)\
                       .with_entities(*PROJECTION_OF_BASH_NEED_TO_DISPLAY_ON_WEB)\
                       .order_by(Bash.id.desc())\
                       .limit(limit).offset(page)\
                       .all()
    # res=[]
    # for bash in bashes:
    #    res.append(combine(vars(bash)))
    return bashes

def find_one(db_session=db.session):
    return db_session.query(Bash)\
                     .with_entities(*PROJECTION_OF_BASH_USER_COULD_MODIFY)\
                     .limit(1).first()

def get_bash_column_metadata():
    limitition_for_user = set(k.name for k in PROJECTION_OF_BASH_USER_COULD_MODIFY)
    return {c.name: c.type.python_type for c in Bash.__table__.columns if c.name in limitition_for_user}

# .with_entities(*PROJECTION_OF_BASH_NEED_TO_DISPLAY_ON_WEB)\
# argument is a dic
def add_bash(db_session=db.session, **kwargs):
    # kwargs
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
    bash = db_session.query(Bash).filter_by(id = id).options(load_only(attr)).first()
    bash = vars(bash)
    value = bash[attr] 
    return value


def add_job_id_to_bash_db(bashid, jobid, db_session=db.session, command=None):
    bash = db_session.query(Bash).filter_by(id = bashid).options(load_only('id','rqids', 'command')).first()
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
    API_CHECK_HAS_LAYER = 'http://52.90.74.236:65533//minty/has_layer/'
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
    
    def check_has_layer(uuid2, dataset_id, viz_config):
        req = requests.get(API_CHECK_HAS_LAYER + uuid2)
        if req.status_code != 200:
            return 'Failed request to has_layer,\ncannot check if minty has layer or not.\nDataset_id: %s\nViz_config: %s' % (dataset_id, viz_config)
        
        response = req.json()
        # print(response)
        if not isinstance(response, dict):
            return 'has_layer return error.\nDataset_id: %s\nViz_config: %s' % (dataset_id, viz_config)
        
        if response['has'] is False:
            return 'Failed in pipeline: not generate the layer.\nDataset_id: %s\nViz_config: %s' % (dataset_id, viz_config)

        return 'success'

    db_session = get_db_session_instance()
    bash = db_session.query(Bash).filter_by(id = bash_id).first()
    update_to_dc = ''

    check_layer = check_has_layer(bash.md5vector, bash.dataset_id, bash.viz_config)

    if check_layer == 'success':
        check_layer = 'Layer check success.\nDataset_id: %s\nViz_config: %s' % (bash.dataset_id, bash.viz_config)
        if update_viz_status_to_dc(bash.dataset_id, bash.viz_config) == 'success':
            update_to_dc = 'Update viz status to data catalog success.\nDataset_id: %s\nViz_config: %s' % (bash.md5vector, bash.viz_config)
        else:
            update_to_dc = 'Error in updating viz status to data catalog.\nDataset_id: %s\nViz_config: %s' % (bash.md5vector, bash.viz_config)

    _j = Job.fetch(job_id, connection=rq_connection)
    
    if _j.exc_info:
        logs['exc_info'] = str(_j.exc_info) + '\n\n' + check_layer + '\n\n' + update_to_dc
    else:
        logs['exc_info'] = check_layer + '\n\n' + update_to_dc

    bash.rqids = job_id
    bash.status = _j.get_status()
    bash.logs = json.dumps(logs)

    db_session.commit()
    path = bash.dir
    if path == '':
        path = bash.data_file_path
    else:
        path = path + '/'
    
    abspath = os.path.abspath(os.path.expanduser(path)).replace('*', '')

    if abspath.startswith('/tmp/') and len(abspath) > len('/tmp/'):
        if bash.dir:
            if os.path.isdir(abspath):
                import shutil
                shutil.rmtree(abspath, ignore_errors=True)
        else:
            if os.path.exists(abspath) and not os.path.isdir(abspath):
                os.remove(abspath)
        # subprocess.run(["bash", "rm", "-rf", path])

    return bash

