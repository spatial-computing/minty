from exts import db
from sqlalchemy.sql import func
from sqlalchemy import text
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.hybrid import hybrid_property , hybrid_method

db = SQLAlchemy()

class Original(db.Model):
    __tablename__='original'

    id=db.Column(db.Integer,primary_key=True,nullable=False)
    dataset_name=db.Column(db.String(255))
    filename=db.Column(db.String(255),nullable=False)
    filepath=db.Column(db.String(255),nullable=False)
    gdalinfo=db.Column(db.Text)
    related_json=db.Column(db.Text)
    create_at = db.Column(db.DateTime(timezone=False), server_default=func.now())
    modified_at = db.Column(db.DateTime(timezone=False), onupdate=func.now())
        

class Metadata(db.Model):
    __tablename__='metadata'

    k=db.Column(db.String(32),nullable=False,primary_key=True)
    v=db.Column(db.Text)

    @hybrid_property
    def getter(self):
        return self.k == 'test'

    #offset get and update where k = offset 

class Tileserverconfig(db.Model):
    __tablename__='tileserverconfig'

    id=db.Column(db.Integer,primary_key=True,nullable=False)
    layerid=db.Column(db.String(255),nullable=False)
    mbtiles=db.Column(db.String(255),nullable=False)
    md5=db.Column(db.String(255),nullable=False)  

class Layer(db.Model):
    __tablename__='layer'

    id=db.Column(db.Integer,nullable=False,primary_key=True)
    layerid=db.Column(db.String(255),nullable=False,server_default='')
    processing_flag=db.Column(db.SmallInteger,server_default=text('0'))
    isdiff=db.Column(db.SmallInteger,server_default=text('0'))
    diff_layerid=db.Column(db.String(255),nullable=False,server_default='')
    original_id=db.Column(db.Integer)
    type=db.Column(db.String(8),server_default='vector')
    tileformat=db.Column(db.String(8),server_default='pdf')
    name=db.Column(db.String(255),nullable=False)
    stdname=db.Column(db.String(255),nullable=False)
    md5=db.Column(db.String(255),nullable=False)
    sourcelayer=db.Column(db.String(64),nullable=False)
    hasdata=db.Column(db.SmallInteger,server_default=text('0'))
    hastimeline=db.Column(db.SmallInteger,server_default=text('0'))
    maxzoom=db.Column(db.Integer,server_default=text('14'))
    minzoom=db.Column(db.Integer,server_default=text('3'))
    bounds=db.Column(db.String(255))
    mbfilename=db.Column(db.String(255))
    directory_format=db.Column(db.String(255))
    starttime=db.Column(db.DateTime,server_default=text('NULL'))
    endtime=db.Column(db.DateTime,server_default=text('NULL'))
    json_filename=db.Column(db.String(255))
    server=db.Column(db.String(255))
    tileurl=db.Column(db.String(255))
    legend=db.Column(db.TEXT)
    uri=db.Column(db.TEXT)
    valuearray=db.Column(db.TEXT)
    vector_json=db.Column(db.TEXT)
    colormap=db.Column(db.TEXT)
    hotspot=db.Column(db.TEXT)
    original_dataset_bounds=db.Column(db.TEXT)
    mapping=db.Column(db.String(64))
    create_at = db.Column(db.DateTime, server_default=func.now())
    modified_at = db.Column(db.DateTime, server_default=func.now())
    steptype=db.Column(db.String(32),server_default='NULL')
    stepoption_type=db.Column(db.String(16),server_default='NULL')
    stepoption_format=db.Column(db.String(16),server_default='NULL')
    step=db.Column(db.String(255),server_default='NULL')
    axis=db.Column(db.String(32),server_default='NULL')
