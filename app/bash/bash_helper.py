import os
import subprocess
import yaml
import pymongo
import json
import redis
from redis import Redis
from app.models import Bash, db
from app.jobs import rq_run_command_job, rq_instance, rq_terminate_mintcast_session
from sqlalchemy.orm import load_only



MINTCAST_PATH = os.environ.get('MINTCAST_PATH')
COLUMN_NAME_DATA_FILE_PATH = 'data_file_path'
COLUMN_NAME_VIZ_TYPE = 'viz_type'

BASH_DISPLAY_ON_TABLE_SEARCH_FILTERS = [
            Bash.id, 
            Bash.command, 
            Bash.rqids, 
            Bash.viz_config, 
            Bash.viz_type, 
            Bash.file_type, 
            Bash.md5vector, 
            Bash.download_ids, 
            Bash.after_run_ids, 
            Bash.dataset_id
]

BASH_DISPLAY_ON_TABLE = [
            'id', 
            'command', 
            'rqids', 
            'viz_config', 
            'viz_type', 
            'file_type', 
            'md5vector', 
            'download_ids', 
            'after_run_ids', 
            'dataset_id'
]

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
    'download_ids',
    'after_run_ids',
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
        Bash.md5vector,
        Bash.download_ids,
        Bash.after_run_ids,
        Bash.dataset_id
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

PROJECTION_OF_BASH_TO_USE = [
    Bash.viz_config, 
    Bash.dataset_id, 
    Bash.id, 
    Bash.data_url, 
    Bash.viz_type,
    Bash.data_file_path,
    Bash.dir,
    Bash.status
]
def combine( args ):

    mongo_client = pymongo.MongoClient(MONGODB_CONNECTION)
    mongo_db = mongo_client["mintcast"]
    mongo_mintcast_default = mongo_db["metadata"]
    default_setting = mongo_mintcast_default.find_one({'type': 'minty-mintcast-cmd-parameter-setting'}, {"_id": False, "type":False})
    default_setting_controller = mongo_mintcast_default.find_one({'type': 'minty-dashboard-setting'}, {"_id": False, "type":False})
    if (default_setting_controller['use_default_setting']):
        for key in default_setting:
            # if key != 'use_default_setting':
            args[key] = default_setting[key] 

    res = " "
    for key in args:
        if( key not in IGNORED_KEY_AS_PARAMETER_IN_COMMAND and args[key] not in {'', None, False}):
            param = key.replace("_", "-")
            if( args[key] == True ):
                res += "--%s " % (param)
            else:
                if key in MINTCAST_PATH_NEEDED_IN_COMMAND:
                    res += "--%s %s%s " % (param, MINTCAST_PATH.strip().rstrip('/') + '/', args[key])
                elif key == 'dir':
                    res += "--%s %s " % (param, args[key])
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

def find_bash_by_id_for_run(id, db_session=db.session):
    bash = db_session.query(Bash)\
                     .with_entities(*PROJECTION_OF_BASH_TO_USE)\
                     .filter_by(id = id).first()
    return bash

def find_count(db_session=db.session):
    return db_session.query(Bash).count()

def find_bash_by_viz_config_for_run(viz_config, db_session=db.session):
    bash = db_session.query(Bash)\
                     .with_entities(*PROJECTION_OF_BASH_TO_USE)\
                     .filter_by(viz_config = viz_config).first()
    return bash
#find all
def find_all(limit = 20, page=0, db_session=db.session):
    bashes = db_session.query(Bash)\
                       .with_entities(*PROJECTION_OF_BASH_NEED_TO_DISPLAY_ON_WEB)\
                       .order_by(Bash.id.desc())\
                       .limit(limit).offset(limit*page)\
                       .all()
    # res=[]
    # for bash in bashes:
    #    res.append(combine(vars(bash)))
    return bashes

def find_all_bashes(db_session=db.session):
    bashes = db_session.query(Bash)\
                       .with_entities(*BASH_DISPLAY_ON_TABLE_SEARCH_FILTERS)\
                       .order_by(Bash.id.desc())\
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
    
    # newbash.command = combine(vars(newbash))
    db_session.add(newbash)
    db_session.flush()
    db_session.commit()
   
    r = Redis.from_url(rq_instance.redis_url,decode_responses=True)
    expire_time = get_expire_time(r)
    if expire_time != -1:
        bash_on_table = dict()
        newbash = vars(newbash)
        for key in BASH_DISPLAY_ON_TABLE:
            bash_on_table[key] = newbash[key]
        add_bash_to_redis(bash_on_table,expire_time,r)    
    return newbash

def get_expire_time(r = Redis.from_url(rq_instance.redis_url,decode_responses=True)):
    redis_key_list = r.scan(match='minty:*',count=1)[1]
    if redis_key_list:
        return r.ttl(redis_key_list[0])
    else:
        return -1

def add_bash_to_redis(bash_on_table, expire_time,r = Redis.from_url(rq_instance.redis_url,decode_responses=True)):
    
    redis_key_md5vector = "minty:bash:search:"+bash_on_table['md5vector']
    redis_key_dataset_id = "minty:bash:search:"+bash_on_table['dataset_id']
    bash_id = str(bash_on_table['id'])
    redis_key_bash_id = "minty:bash:bashid:"+bash_id
    r.setex(redis_key_md5vector,expire_time,redis_key_bash_id)
    r.setex(redis_key_dataset_id,expire_time,redis_key_bash_id)
    r.hmset(redis_key_bash_id,bash_on_table)
    r.expire(redis_key_bash_id,expire_time)      

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

    r = Redis.from_url(rq_instance.redis_url,decode_responses=True)
    expire_time = get_expire_time(r)
    if expire_time != -1:
        bash_on_table = dict()
        bash = vars(bash)
        for key in BASH_DISPLAY_ON_TABLE:
            bash_on_table[key] = bash[key]
        add_bash_to_redis(bash_on_table,expire_time,r) 
    return bash


def find_bash_attr(id, attr, db_session=db.session):
    bash = db_session.query(Bash).filter_by(id = id).options(load_only(attr)).first()
    value = None
    if bash:
        bash = vars(bash)
        value = bash[attr] 
    return value
    
def find_bash_attrs(id,attrs):
    bash = db.session.query(Bash).filter_by(id = id).options(load_only(*attrs)).first()
    if not bash:
        return []
    bash = vars(bash)
    value=[]
    for attr in attrs:
        value.append(bash[attr])
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

def cancel_mintcast_job(bash_id):
    job = rq_terminate_mintcast_session.queue(bash_id, rq_instance.redis_url, _after_terminated)

def _after_terminated(bash_id, success=True, msg=''):
    from app.models import get_db_session_instance
    db_session = get_db_session_instance()
    if success:
        update_bash(bash_id, db_session=db_session, status="ready_to_run") 
    else:
        update_bash(bash_id, db_session=db_session, status="failed", logs=json.dumps({'exc_info': msg}))


def update_bash_status(bash_id, job_id, logs, rq_connection):
    from app.models import get_db_session_instance
    from rq.job import Job
    import requests
    API_UPDATE_VIZSTATUS_TO_DC = 'http://api.mint-data-catalog.org/datasets/update_dataset_viz_status'
    API_CHECK_HAS_LAYER = 'http://minty.mintviz.org/minty/has_layer/'
    API_CHECK_MINT_CHART_LAYER = 'http://minty.mintviz.org/minty/chart/'
    def update_viz_status_to_dc(dataset_id, viz_config):
        payload = {
                'dataset_id': dataset_id, 
                'viz_config_id': viz_config,
                '$set': {
                        'visualized' : True
                    }
                }
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
    def utc_to_local(utc_dt):
        from datetime import timezone
        return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)

    def check_has_layer(uuid2, dataset_id, viz_config, viz_type, db_session):
        req = None
        if viz_type == 'mint-chart':
            req = requests.get(API_CHECK_MINT_CHART_LAYER + uuid2)
        else:
            req = requests.get(API_CHECK_HAS_LAYER + uuid2)
        
        if req.status_code != 200:
            return 'Failed request to check layer,\ncannot check if minty has layer or not.\nDataset_id: %s\nViz_config: %s' % (dataset_id, viz_config)
        
        response = req.json()
        # print(response)
        if not isinstance(response, dict):
            return 'has_layer return error.\nDataset_id: %s\nViz_config: %s' % (dataset_id, viz_config)

        from datetime import datetime, timedelta
        if viz_type == 'mint-chart':
            if response.get('status') != None and response['status'] == 404:
                return 'Viz_type : mint-chart, cannot find the layer with this uuid.\nDataset_id: %s\nViz_config: %s' % (dataset_id, viz_config)
            elif (response.get('data') == None) or (response.get('data') != None and len(response['data']) == 0):
                return 'Viz_type : mint-chart, the layer with this uuid return the wrong data content.\nDataset_id: %s\nViz_config: %s' % (dataset_id, viz_config)

            layer_modified_at = response.get('modified_at', None)
            if layer_modified_at:
                layer_modified_at = utc_to_local(datetime.strptime(layer_modified_at, '%Y-%m-%d %H:%M:%S'))
            else:
                layer_modified_at = utc_to_local(datetime.utcnow())
        else:
            if response['has'] is False:
                return 'Failed in pipeline: not generate the layer.\nDataset_id: %s\nViz_config: %s' % (dataset_id, viz_config)
            layer_modified_at = find_modified_at_by_md5vector(uuid2, db_session)

        from rq import get_current_job
        
        job = get_current_job()

        job_enqueued_at = utc_to_local(job.enqueued_at.replace(second=0, microsecond=0)) - timedelta(minutes=10)
        layer_modified_at = layer_modified_at

        time_comparision = "\njob_enqueued_at: %s\nlayer_modified_at: %s" % (datetime.strftime(job_enqueued_at,'%Y-%m-%d %H:%M:%S %f %z'), datetime.strftime(layer_modified_at,'%Y-%m-%d %H:%M:%S %f %z'))

        if job_enqueued_at > layer_modified_at:
            return "Failed to run the command, the job enqueued_at time is later than the layer updated." + time_comparision

        return 'success'

    def find_modified_at_by_md5vector(md5vector, db_session):
        from app.models import Layer
        from sqlalchemy.orm import load_only
        layer = db_session.query(Layer).filter_by(md5 = md5vector).options(load_only('id', 'modified_at')).first()
        if layer:
            return layer.modified_at.astimezone(tz=None)
        else:
            return utc_to_local(datetime.utcnow())

    db_session = get_db_session_instance()
    bash = db_session.query(Bash).filter_by(id = bash_id).first()
    bash.rqids = job_id
    db_session.commit()
    
    update_to_dc = ''
    check_layer = check_has_layer(bash.md5vector, bash.dataset_id, bash.viz_config, bash.viz_type, db_session)
    
    if check_layer == 'success':
        check_layer = 'Layer check success.\nDataset_id: %s\nViz_config: %s' % (bash.dataset_id, bash.viz_config)
        bash.status = 'success'
        if update_viz_status_to_dc(bash.dataset_id, bash.viz_config) == 'success':
            update_to_dc = 'Update viz status to data catalog success.\nDataset_id: %s\nViz_config: %s' % (bash.dataset_id, bash.viz_config)
        else:
            update_to_dc = 'Error in updating viz status to data catalog.\nDataset_id: %s\nViz_config: %s' % (bash.dataset_id, bash.viz_config)
    else:
        bash.status = 'failed'

    _j = Job.fetch(job_id, connection=rq_connection)
    
    if _j.exc_info:
        logs['exc_info'] = str(_j.exc_info) + '\n\n' + check_layer + '\n\n' + update_to_dc
    else:
        logs['exc_info'] = check_layer + '\n\n' + update_to_dc

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
