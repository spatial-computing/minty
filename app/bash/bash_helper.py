
import os
MINTCAST_PATH = os.environ.get('MINTCAST_PATH')

from app.models import Bash, db
from app.job import rq_run_job, rq_excep_job, rq_add_job

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
    # _get_value = None
    # if isinstance(args, dict):
    #   _get_value = args.__getitem__
    # else:
    #   _get_value = args.__getattribute__  
    for key in args:
        if( key not in IGNORED_KEY_AS_PARAMETER_IN_COMMAND and args[key] not in {'', None, False}):
            param = key.replace("_", "-")

            if( args[key] == True ):
                res += "--%s " % (param)
            else:
                if key in MINTCAST_PATH_NEEDED_IN_COMMAND:
                    res += "--%s '%s%s' " % (param, MINTCAST_PATH.strip().rstrip('/') + '/', args[key])
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


def add_job_id_to_bash_db(bashid, jobid, db_session=db.session):
    bash = db_session.query(Bash).filter_by(id = bashid).first()
    setattr(bash, "rqids", jobid)
    db_session.commit()

def run_bash(bashid):
    command = find_command_by_id(bashid)
    job = add_job_id_to_bash_db.queue(command)
    # job = excep.queue()
    #job = add.queue(1, 2, bashid)
    add_job_id(bashid, job.id)

def find_one(db_session=db.session):
    return db_session.query(Bash).first()

