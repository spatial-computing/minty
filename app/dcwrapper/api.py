import requests
import json
import os
# import magic
from datetime import timedelta

from app.models import db, DataSet, Bash
from app.job import rq_instance, rq_download_job, rq_run_command_job, rq_create_bash_job, rq_check_job_status_scheduler
from app.bash import bash_helper
from rq import Connection, Worker, Queue
from rq.utils import parse_timeout


HEADERS = {'Content-Type': 'application/json', 'cache-control': 'no-cache', 'Postman-Token': '3084e843-b082-4bfb-be1a-bb4ac72c865'}
API_URL = 'http://api.mint-data-catalog.org/datasets'
API_STANDARD_NAME = API_URL + '/dataset_standard_variables'
API_FIND_RESOURCES = API_URL + '/find'
API_FIND_DATASETS = 'http://api.mint-data-catalog.org/find_datasets'

# Scheduler
RQ_SCHEDULER_START_IN_SECONDS = 5
RQ_SCHEDULER_REPEAT_TIMES = parse_timeout('1d') / 60  # Repeat this number of times (None means repeat forever)
RQ_SCHEDULER_INTERVAL = 5

class DCWrapper(object):
    def __init__(self, bash_autorun=True, download_dist='/tmp/mint_datasets'):
        self.bash_autorun = bash_autorun
        X_API_KEY = requests.get('https://api.mint-data-catalog.org/get_session_token') 
        X_API_KEY = X_API_KEY.json()
        if 'X-Api-Key' in X_API_KEY:
            X_API_KEY = X_API_KEY['X-Api-Key']
        else:
            X_API_KEY = ""
        HEADERS['X-Api-Key'] = X_API_KEY
        self.download_dist = download_dist
        if not os.path.exists(self.download_dist):
            os.mkdir(self.download_dist)
        self.command_args = {}

    def findByDatasetId(self, dataset_id):
        status = 200
        req = None
        if not isinstance(dataset_id, str):
            print('invalid input')
            status = 404
            return status

        # payload = {'dataset_id': dataset_id}
        # req = requests.post(API_STANDARD_NAME, headers = HEADERS, data = json.dumps(payload))
        # if req.status_code != 200:
        #     status = 404.1
        #     return status

        # response = req.json()
        # if isinstance(response, dict) and 'error' in response:
        #     print(response['error'])
        #     status = 404.1
        #     return status

        # std = json.dumps(response['dataset']['standard_variables'])
        #print(std)
        # dataset = DataSet(id=response['dataset']['id'], name=response['dataset']['name'], standard_variables=std)
        # check = db.session.query(DataSet).filter_by(id=response['dataset']['id']).first()
        # if not check:
        #     db.session.add(dataset)
        #     db.session.commit()

        dataset = self.findDatasetById(dataset_id)
        if dataset == 'error':
            status = 404.2
            return status

        resources = self.findResourcesById(dataset_id)
        if resources == 'error':
            status = 404.3
            return status

        arr = []
        for k, v in dataset['dataset_metadata'].items():
            if k.startswith('viz_config'):
                arr.append(k)
        if len(arr) == 0:
            status = 404.4
            return status
        arr.sort()

        #print(arr)
        the_first_viz_config = arr[0]
        metadata = dataset['dataset_metadata'][the_first_viz_config]

    # "mint-chart", 
    # "mint-map", 
    # "mint-map-time-series"
        
        command_args = {
            "layer_name": metadata['metadata']['title'].strip().replace(' ', '~_~').replace('\t','~_~'),
            "viz_config": the_first_viz_config,
            "viz_type": metadata['viz_type']
        }
        if metadata['viz_type'] != 'mint-chart':
            command_args.update({
                "md5vector": dataset['dataset_id'],
                "file_type": metadata['metadata']['file-type'],
            })
        else:
            # Bar Dot Donut
            command_args['chart_type'] = metadata['metadata']['chart-type'].lower()
        # Black2White BuPu YlGnBl
        # South Sudan Pongo Basin No Clip

        if metadata['metadata']['shapefile'] == "South Sudan":
            command_args["with_shape_file"] = "shp/ss.shp"
        elif metadata['metadata']['shapefile'] == "Pongo Basin":
            command_args["with_shape_file"] = "shp/WBD.shp"
        elif metadata['metadata']['shapefile'] == "Gel-Aliab":
            command_args["with_shape_file"] = "shp/GelAliab.shp"
        
        command_args["load_colormap"] = "shp/colortable.txt"
        if metadata['metadata']['color-map'] == "Black2White":
            command_args["load_colormap"] = "shp/colortable.txt"
        elif metadata['metadata']['color-map'] == "BuPu":
            command_args["load_colormap"] = "shp/bupu_colormap.txt"
        elif metadata['metadata']['color-map'] == "YlGnBl":
            command_args["load_colormap"] = "shp/ylgnbl_colormap.txt"

        viz_type = 'tiff'
        if metadata['metadata']['file-type'] == 'netcdf':
            command_args['netcdf_subdataset'] = metadata['metadata']['netcdf-subdataset']
            if metadata['viz_type'] == 'mint-map':
                command_args['type'] = 'single-netcdf'
            elif metadata['viz_type'] == 'mint-map-time-series':
                command_args['type'] = 'netcdf'
        elif metadata['metadata']['file-type'] == 'geotiff':
            if metadata['viz_type'] == 'mint-map':
                command_args['type'] = 'tiff'
            elif metadata['viz_type'] == 'mint-map-time-series':
                command_args['type'] = 'tiff-time'
        elif metadata['metadata']['file-type'] == 'csv':
                command_args['type'] = 'csv'
        #metadata['viz_type'] = 'abc'
        if metadata['viz_type'] == 'mint-map-time-series':
            command_args.update({
                "output_dir_structure": metadata['metadata']['directory-structure'],
                "directory_structure":metadata['metadata']['directory-structure'],
                "start_time": metadata['metadata']['start-time'],
                "end_time": metadata['metadata']['end-time'],
                "datatime_format": metadata['metadata']['datatime-format'],
                "dir": self.download_dist + '/' + dataset_id,
            })
        else:
            if len(resources) == 1:
                command_args['data_file_path'] = 'single file tag'
        #print(command_args)
        self.command_args = command_args

        download_status = self._download(resources, dataset_id, **command_args)
        if download_status == 'done_queue':
            status = 200
        else:
            status = 500

        return status
        
    def findResourcesById(self, dataset_id):
        payload = {'dataset_ids__in': [dataset_id], 'limit': 1}
        req = requests.post(API_FIND_RESOURCES, headers = HEADERS, data = json.dumps(payload))

        if req.status_code != 200:
            return 'error'

        response = req.json()
        if not isinstance(response, dict):
            return 'error'

        if 'error' in response:
            print(response['error'])
            return 'error'

        if len(response['resources']) == 0 :
            return 'error'

        return response['resources']

    def findDatasetById(self, dataset_id):
        if isinstance(dataset_id, str):
            dataset_id = [dataset_id]
        payload = {'dataset_ids__in': dataset_id}
        req = requests.post(API_FIND_DATASETS, headers = HEADERS, data = json.dumps(payload))
        
        if req.status_code != 200:
            return 'error'
        
        response = req.json()
        if not isinstance(response, dict):
            return 'error'

        if 'error' in response:
            print(response['error'])
            return 'error'

        
        if len(response['datasets']) == 0:
            return 'error'

        return response['datasets'][0]

    def _download(self, resource_list, dataset_id, **commmand_args):
        #print(len(resource_list))
        #print(os.getcwd())
        dir_path = self.download_dist + '/' + dataset_id
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)
        jobs = []
        for index, resource in enumerate(resource_list):
            _j = rq_download_job.queue(resource, dataset_id, index, dir_path)
            jobs.append(_j.id)
        # scheduler = rq_instance.get_scheduler()
        schedule = rq_check_job_status_scheduler.schedule(
                timedelta(seconds=RQ_SCHEDULER_START_IN_SECONDS), # queue job in seconds
                jobs,
                self._after_download,
                rq_instance.redis_url,
                description="Download status checking scheduler",
                repeat=RQ_SCHEDULER_REPEAT_TIMES, # The number of times the job needs to be repeatedly queued. Requires setting the interval parameter.
                interval=RQ_SCHEDULER_INTERVAL # The interval of repetition as defined by the repeat parameter in seconds.
                )
        # bash_create_job = rq_create_bash_job.queue(self, **command_args)
        print('done download enqueue')
        return 'done_queue'

    def _buildBash(self, db_session, **kwargs):
        bash_check = db_session.query(Bash).filter_by(md5vector=kwargs['md5vector'], viz_config=kwargs['viz_config']).first()

        if kwargs['data_file_path'] == 'single file tag':
            single_file_dir = self.download_dist + '/' + kwargs['md5vector']
            data_file_path = self._magicfile_check(single_file_dir, kwargs['file_type'], kwargs['md5vector'])
            print('only 1 file name: %s' % data_file_path)
            kwargs['data_file_path'] = data_file_path

        if not bash_check:
            bash = bash_helper.add_bash(db_session=db_session, **kwargs)
            return bash
        else:
            bash = bash_helper.update_bash(bash_check.id, db_session=db_session, **kwargs)
            return bash

    def _after_download(self, redis_url):
        from app.models import get_db_session_instance
        db_session = get_db_session_instance()

        bash = self._buildBash(db_session, **self.command_args)
        if self.bash_autorun:
            bash = db_session.query(Bash).filter_by(md5vector=bash.md5vector).first()
            
            command = bash_helper.find_command_by_id(bash.id, db_session=db_session)
            from app.job import queue_job_with_connection
            from redis import Redis
            rq_connection = Redis.from_url(redis_url)
            bash_job = queue_job_with_connection(
                rq_run_command_job, 
                rq_connection, 
                command, 
                bash.id,
                redis_url
            )
            
            bash_helper.add_job_id_to_bash_db(bash.id, bash_job.id, db_session=db_session)
            print('bash run enqueue')

    def _magicfile_check(self, single_file_dir, file_type, dataset_id):
        ONLY_CHECK_SUFFIX = {
            'geojson',
            'csv'
        }
        FILE_TYPE_TO_SUFFIX = {
            'geojson' : {'geojson', 'json'},
            'csv' : {'csv'}, 
            'netcdf' : {'nc'},
            'geotiff': {'tif', 'tiff', 'asc'}
        }
        FILE_TYPE_TO_MAGIC = {
            'netcdf': [ 'NetCDF Data Format', 'Hierarchical Data Format'],
            'geotiff': [ 'TIFF image data' ]
        }
        for root, dirs, files in os.walk(single_file_dir):
            for name in files:
                filename = os.path.join(root, name)
                if file_type in ONLY_CHECK_SUFFIX:
                    suffix = self._check_suffix(filename)
                    if suffix in FILE_TYPE_TO_SUFFIX[file_type.lower()]:
                        return filename
                else:
                    fm = magic.from_file(filename)
                    for mgx in FILE_TYPE_TO_MAGIC[file_type.lower()]:
                        if fm.startswith(mgx):
                            return filename
                    # check type
                    suffix = self._check_suffix(filename)
                    if suffix in FILE_TYPE_TO_SUFFIX[file_type.lower()]:
                        return filename

        raise FileNotFoundError("%s doesn't have any valid file" % (dataset_id))
        return None
        
    def _check_suffix(self, filename):
        lower_name = filename.lower()
        suffix = lower_name.split('.')
        if len(suffix) > 0:
            return suffix[-1]
        return ''



"""
def getNews(self, offset):
		# get all new dataset since offset		
		pass

	def findByTask(self, task_type):
		# task
		#  |- single dataset
		#  |- timeseries
		#  |- diff
		#  |- trend  => chart
		#  |- chart
		pass

	def findById(self, id):
		# get all metadata
		# put into postgres mintcast.datacatalog
		# download 
		pass

	def findByName(self, name):
		# $.post
		pass

	def notifyById(self, id, msg):
		pass

	def _download(self, url):
		"insert into mintcast.original"
		"rq"
		pass

	def _download_timeseries(self, url):

		pass

	def _download_zip(self, url):

		pass
# views.py

class Mintcast():
	#docstring for mintcast#
	def __init__(self, arg):
		pass

	def handleTiff(self, **kargs):
		# karg {}
		pass

	def handleTimeseries(self, **kargs):

		pass
	
# User
#  |- dashboard
	#  |- rq task list name : status
	#  |- mintcast.original (find, update)  
	#  |- [button]=> start mintcast job

class mintUIrequest(methodview):
	#docstring for mintUIrequest
	def __init__(self):
		pass

	def hasID(self, id):
		# check mintcast.layer has dcid=id
		return True

	def get(self, id):
		if hasID(id):
			return jsonify({'status': 'ok','name': mintcast.layer.sourcelayer, 'md5': mintcast.layer.md5})
		else:
			# bootstrap


			# create job 
				# |- request DC wrapper
				# |- download Dataset
				if timeseries:
					# |- request timeseries format
					if empty:
						# |- wait
				# |- generate mintcast job use parameter dependon

			return jsonify({'status': '404'})
            """