from sqlalchemy.sql import func
from sqlalchemy import text
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.hybrid import hybrid_property , hybrid_method

db = SQLAlchemy()

def get_db_session_instance():
    from database import PostgresConfig
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(PostgresConfig.POSTGRES_CONNECTION).connect()
    Session = sessionmaker(bind=engine)
    session = Session()
    return session

class Original(db.Model):
    __tablename__='original'

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    dataset_name = db.Column(db.String(255))
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(255), nullable=False)
    gdalinfo = db.Column(db.Text)
    related_json = db.Column(db.Text)
    create_at = db.Column(db.DateTime(timezone=False), server_default=func.now())
    modified_at = db.Column(db.DateTime(timezone=False), onupdate=func.now())
        

class Metadata(db.Model):
    __tablename__='metadata'

    k = db.Column(db.String(32), nullable=False, primary_key=True)
    v = db.Column(db.Text)

    @hybrid_property
    def getter(self):
        return self.k == 'test'

    #offset get and update where k = offset 

class Tileserverconfig(db.Model):
    __tablename__ = 'tileserverconfig'

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    layerid = db.Column(db.String(), nullable=False)
    mbtiles = db.Column(db.String(), nullable=False)
    md5 = db.Column(db.String(255), nullable=False)
    layer_name = db.Column(db.String(), nullable=False)  

class Layer(db.Model):
    __tablename__='layer'

    id = db.Column(db.Integer, nullable=False, primary_key=True)
    layerid = db.Column(db.String(255), nullable=False, server_default='')
    processing_flag = db.Column(db.SmallInteger, server_default=text('0'))
    isdiff = db.Column(db.SmallInteger, server_default=text('0'))
    diff_layerid = db.Column(db.String(255), nullable=False, server_default='')
    original_id = db.Column(db.Integer)
    type = db.Column(db.String(8), server_default='vector')
    tileformat = db.Column(db.String(8), server_default='pdf')
    name = db.Column(db.String(255), nullable=False)
    stdname = db.Column(db.String(255), nullable=False)
    md5 = db.Column(db.String(255), nullable=False)
    sourcelayer = db.Column(db.String(), nullable=False)
    hasdata = db.Column(db.SmallInteger, server_default=text('0'))
    hastimeline = db.Column(db.SmallInteger, server_default=text('0'))
    maxzoom = db.Column(db.Integer, server_default=text('14'))
    minzoom = db.Column(db.Integer, server_default=text('3'))
    bounds = db.Column(db.String(255))
    mbfilename = db.Column(db.String(255))
    directory_format = db.Column(db.String(255))
    starttime = db.Column(db.DateTime, server_default=text('NULL'))
    endtime = db.Column(db.DateTime, server_default=text('NULL'))
    json_filename = db.Column(db.String(255))
    server = db.Column(db.String(255))
    tileurl = db.Column(db.String(255))
    legend = db.Column(db.TEXT)
    uri = db.Column(db.TEXT)
    valuearray = db.Column(db.TEXT)
    vector_json = db.Column(db.TEXT)
    colormap = db.Column(db.TEXT)
    layer_type = db.Column(db.Integer,server_default = text('100'))
    original_dataset_bounds = db.Column(db.TEXT)
    mapping = db.Column(db.String())
    create_at = db.Column(db.DateTime, server_default=func.now())
    modified_at = db.Column(db.DateTime, server_default=func.now())
    steptype = db.Column(db.String(32), server_default='NULL')
    stepoption_type = db.Column(db.String(), server_default='NULL')
    stepoption_format = db.Column(db.String(), server_default='NULL')
    step = db.Column(db.String(255), server_default='NULL')
    axis = db.Column(db.String(32), server_default='NULL')
    dcid = db.Column(db.String(255), server_default='')
    styletype =  db.Column(db.String(32), server_default='fill')
    legend_type = db.Column(db.String(16), server_default='linear')
    viz_type = db.Column(db.TEXT, server_default='')
    title = db.Column(db.TEXT, server_default='')

class Bash(db.Model):
    __tablename__='bash'

    id = db.Column(db.Integer, nullable=False, primary_key=True)
    type = db.Column(db.String(255), server_default='')
    qml = db.Column(db.String(255), server_default='')
    dir = db.Column(db.String(), server_default='')
    md5vector = db.Column(db.String(255), server_default='')
    
    output_dir_structure = db.Column(db.String(), server_default='')
    start_time = db.Column(db.String(255), server_default='')
    end_time = db.Column(db.String(255), server_default='')
    datatime_format = db.Column(db.String(255), server_default='')
    layer_name = db.Column(db.String(), server_default='')
    output = db.Column(db.String(), server_default='')
    bounds = db.Column(db.String(), server_default='')
    first_file = db.Column(db.Boolean, server_default=text('False'))
    time_stamp = db.Column(db.String(255), server_default='')
    time_steps = db.Column(db.String(255), server_default='')
    time_format = db.Column(db.String(255), server_default='')
    target_json_path = db.Column(db.String(), server_default='')
    server = db.Column(db.String(255), server_default='')
    port = db.Column(db.String(255), server_default='')
    bind = db.Column(db.String(255), server_default='')
    with_shape_file = db.Column(db.String(255), server_default='')
    dev_mode_off = db.Column(db.Boolean, server_default=text('False'))
    tile_server_root = db.Column(db.String(255), server_default='')
    force_restart_tileserver = db.Column(db.String(255), server_default='')
    target_mbtiles_path = db.Column(db.String(255), server_default='')
    scp_to_default_server = db.Column(db.Boolean, server_default=text('False'))
    scp_to_server = db.Column(db.String(255), server_default='')
    without_website = db.Column(db.Boolean, server_default=text('False'))
    tiled_ext = db.Column(db.String(255), server_default='')
    ith_quality_assessment = db.Column(db.Boolean, server_default=text('False'))
    disable_clip = db.Column(db.Boolean, server_default=text('False'))
    disable_new_res = db.Column(db.Boolean, server_default=text('False'))
    disable_raster_tile = db.Column(db.Boolean, server_default=text('False'))
    disable_vector_tile = db.Column(db.Boolean, server_default=text('False'))
    force_proj_first = db.Column(db.Boolean, server_default=text('False'))
    with_south_sudan_shp = db.Column(db.Boolean, server_default=text('False'))
    command = db.Column(db.TEXT, server_default='')
    data_file_path = db.Column(db.String(255), server_default='')

    chart_type = db.Column(db.String(255), server_default='')
    rqids = db.Column(db.String(), server_default='')
    load_colormap = db.Column(db.String(255), server_default='')
    file_type = db.Column(db.String(255), server_default='')
    directory_structure = db.Column(db.String(), server_default='')
    netcdf_subdataset = db.Column(db.String(255), server_default='')
    viz_config = db.Column(db.String(255), server_default='')
    status = db.Column(db.String(255), server_default='not_enqueued')
    viz_type = db.Column(db.String(255), server_default='')
    logs = db.Column(db.TEXT, server_default='')
    dataset_id = db.Column(db.String(255), server_default='')
    data_url = db.Column(db.String(), server_default='')
    download_ids = db.Column(db.String(), server_default='')
    after_run_ids = db.Column(db.String(),server_default='') 
    def __setitem__(self, k, v):
        self.k = v


class DataSet(db.Model):
    __tablename__='dataset'

    id = db.Column(db.String(255), nullable=False, primary_key=True)
    name = db.Column(db.String(255), server_default='')
    standard_variables = db.Column(db.TEXT, server_default='')

    