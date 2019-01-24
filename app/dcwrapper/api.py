import requests
import json
import os
from datetime import timedelta

from app.models import db, DataSet, Bash
from app.job import rq_instance, rq_download_job, rq_run_job, rq_create_bash_job, rq_check_job_status_scheduler
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

        payload = {'dataset_id': dataset_id}
        req = requests.post(API_STANDARD_NAME, headers = HEADERS, data = json.dumps(payload))
        if req.status_code != 200:
            status = 404
            return status

        response = req.json()
        if isinstance(response, dict) and 'error' in response:
            print(response['error'])
            status = 404
            return status

        #db
        std = json.dumps(response['dataset']['standard_variables'])
        #print(std)
        dataset = DataSet(id=response['dataset']['id'], name=response['dataset']['name'], standard_variables=std)
        check = db.session.query(DataSet).filter_by(id=response['dataset']['id']).all()
        if len(check) == 0:
            db.session.add(dataset)
            db.session.commit()

        dataset = self.findDatasetById(dataset_id)
        if dataset == 'error':
            status = 404
            return status

        resources = self.findResourcesById(dataset_id)
        if resources == 'error':
            status = 404
            return status

        arr = []
        for k, v in dataset['dataset_metadata'].items():
            if k.startswith('viz_config_'):
                arr.append(k)
        if len(arr) == 0:
            status = 404
            return status
        arr.sort()

        #print(arr)
        the_first_viz_config = arr[0]
        metadata = dataset['dataset_metadata'][the_first_viz_config]

    # "mint-chart", 
    # "mint-map", 
    # "mint-map-time-series"
        
        command_args = {
            "layer_name": metadata['metadata']['title'].strip().replace(' ', '&nbsp;').replace('\t','&nbsp;'),
            "viz_config": the_first_viz_config
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
        
        command_args["color_map"] = "shp/colortable.txt"
        if metadata['metadata']['color-map'] == "Black2White":
            command_args["color_map"] = "shp/colortable.txt"
        elif metadata['metadata']['color-map'] == "BuPu":
            command_args["color_map"] = "shp/bupu_colormap.txt"
        elif metadata['metadata']['color-map'] == "YlGnBl":
            command_args["color_map"] = "shp/ylgnbl_colormap.txt"

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
        
        if metadata['viz_type'] == 'mint-map-time-series':
            command_args.update({
                "output_dir_structure": metadata['metadata']['directory-structure'],
                "directory_structure":metadata['metadata']['directory-structure'],
                "start_time": metadata['metadata']['start-time'],
                "end_time": metadata['metadata']['end-time'],
                "datatime_format": metadata['metadata']['datatime-format'],
                "dir": download_dist + dataset_id,
            })
        # else:
            # resource = resources[0]
            # file = resource['resource_data_url'].split('/')
            # file_name = file[len(file) - 1]
            # command_args['data_file_path'] = '/tmp/' + dataset_id + '/' +  file_name
        self.command_args = command_args

        download_status = self._download(resources, dataset_id, **command_args)
        if download_status == 'done_queue':
            status = 200
        else:
            status = 500

        return status
        
    def findResourcesById(self, dataset_id):
        payload = {'dataset_ids__in': [dataset_id], 'limit': 20}
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
        dir_path = self.download_dist + dataset_id
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

    def _buildBash(self, **kwargs):
        bash = Bash(**kwargs)
        bashcheck = db.session.query(Bash).filter_by(md5vector=bash.md5vector, viz_config=bash.viz_config).all()
        if len(bashcheck) == 0:
            bash = Bash(**kwargs)
            db.session.add(bash)
            db.session.commit()
            return True
        return False
    def _after_download(self):
        ret = self._buildBash(**self.command_args)
        if self.bash_autorun:
            bash = db.session.query(Bash).filter_by(md5vector=dataset_id).first()
            command = bash_helper.findcommand_by_id(bash.id)
            bashjob = rq_run_job.queue(command)
            bash_helper.add_job_id(bash.id, bashjob.id)
            print('bash run enqueue')

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