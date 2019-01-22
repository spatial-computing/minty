import requests
from app.job import rq
import time
import json
import os 
import urllib
import zipfile
from app.models import db, DataSet, Bash
from app.job import download
from rq import Connection, Worker


HEADERS = {'Content-Type': 'application/json', 'X-Api-Key': 'mint-data-catalog:e038e64c-c950-4fbc-9070-a3e7138b6c4f:dce8a09a-200e-43ca-b996-810c2c437d3a', 'cache-control': 'no-cache', 'Postman-Token': '3084e843-b082-4bfb-be1a-bb4ac72c865'}
API_URL = 'http://api.mint-data-catalog.org/datasets'
class DCWrapper(object):
    def __init__(self):
        self.payload = {}
        self.status = 0

    def findByDatasetId(self, dataset_id):
        req = None
        if not isinstance(dataset_id, str):
            print('invalid input')
            self.status = 404
            return self.status

        self.payload = {'dataset_id': dataset_id}
        req = requests.post(API_URL + '/dataset_standard_variables', headers = HEADERS, data = json.dumps(self.payload))
        response = req.json()
        
        if isinstance(response, dict) and 'error' in response:
            print(response['error'])
            self.status = 404
            return self.status

        #db
        print(response['dataset'])
        std = json.dumps(response['dataset']['standard_variables'])
        #print(std)
        dataset = DataSet(id=response['dataset']['id'], name=response['dataset']['name'], standard_variables=std)
        #db.session.add(dataset)
        #db.session.commit()

        #dowload
        resources = self.findByDatasetIds(dataset_id)
        resource = resources[0]
        metadata = resource['dataset_metadata']['viz_config_1']
        #print(resources)
        #if resources == error
        
        #job = download.queue(resources, dataset_id)
        #print(job.id)
        #print(job.status)
        download = self._download(resources, dataset_id)
        if download == 'done' or download == 'file_exists':
            self.status = 200
        else:
            self.status = 500
        
    # "mint-chart", 
    # "mint-map", 
    # "mint-map-time-series"
        command_args = {
                            "layer_name":metadata['metadata']['title'].strip().replace(' ', '&nbsp;').replace('\t','&nbsp;')
                        }
        if metadata['viz_type'] != 'mint-chart':
            command_args.update({
                "md5vector": resource['dataset_id'],
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
        elif metadata['metadata']['file-type'] == 'tiff':
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
                "dir": '/tmp/' + dataset_id,
            })
        else:
            file = resource['resource_data_url'].split('/')
            file_name = file[len(file) - 1]
            command_args['data_file_path'] = '/tmp/' + dataset_id + '/' +  file_name
        
        self._buildBash(**command_args)
        # TODO try to run
        return self.status

    def _buildBash(self, **kwargs):
        bash = Bash(**kwargs)
        db.session.add(bash)
        db.session.commit()
        
    def findByDatasetIds(self, dataset_id):
        req = None

        self.payload = {'dataset_ids__in': [dataset_id], 'limit': 10000}
        req = requests.post(API_URL + '/find', headers = HEADERS, data = json.dumps(self.payload))
        response = req.json()
        
        if isinstance(response, dict) and 'error' in response:
            print(response['error'])
            return 'error'
        
        return response['resources']

    def _download(self, resource_list, dataset_id):
        print(len(resource_list))
        print(os.getcwd())
        dir_path = '/tmp/' + dataset_id
        if os.path.exists(dir_path):
            print('file_exists')
            return 'file_exists'
        
        os.mkdir(dir_path)
        index = 0
        queue_list = ['download_q1', 'download_q2', 'download_q3', 'download_q4']
        
        for resource in resource_list:
            q = queue_list[index % 4]
            job = download.queue(resource, dataset_id, index, queue=q)
            index += 1

        print('done download queue')
        return 'done'



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