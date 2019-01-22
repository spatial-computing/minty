import requests
from app.job import rq
import time
import json
import os 
import urllib
import zipfile
from app.models import db, DataSet, Bash
from app.job import download


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
        db.session.add(dataset)
        db.session.commit()

        #dowload
        resources = self.findByDatasetIds(dataset_id)
        resource = resources[0]
        metadata = resource['dataset_metadata']['viz_config_1']
        #print(resources)
        #if resources == error
        
        job = download.queue(resources, dataset_id)
        print(job.id)
        print(job.status)
        
        bash = Bash(md5vector=resource['dataset_id'], type=metadata['viz_type'], dir=os.getcwd() + '/app/static/dowloads/' + dataset_id, directory_structure=metadata['metadata']['directory-structure'], output_dir_structure=metadata['metadata']['directory-structure'], start_time=metadata['metadata']['start-time'], end_time=metadata['metadata']['end-time'], datatime_format=metadata['metadata']['datatime-format'], netcdf_subdataset=metadata['metadata']['netcdf-subdataset'], layer_name=metadata['metadata']['title'], with_shape_file=metadata['metadata']['shapefile'], rqids=job.id, color_map=metadata['metadata']['color-map'], file_type=metadata['metadata']['file-type'])
        db.session.add(bash)
        db.session.commit()

        if job.status == 'queued':
            self.status = 200
        else:
            self.status == 500
        
        return self.status

    def _download(self, resource_list, dataset_id):
        print(len(resource_list))
        print(os.getcwd())
        dir_path = os.getcwd() + '/app/static/dowloads/' + dataset_id
        if os.path.exists(dir_path):
            print('file_exists')
            return 'file_exists'
        
        os.mkdir(dir_path)
        index = 1
        for resource in resource_list:
            is_zip = False
            if resource['resource_metadata'].get('is_zip') is not None:
                if resource['resource_metadata']['is_zip'] == 'true':
                    is_zip = True

            file = resource['resource_data_url'].split('/')
            file_name = file[len(file) - 1]
            file_path = dir_path + '/' + file_name

            if is_zip:
                (name, header) = urllib.request.urlretrieve(resource['resource_data_url'], file_path)
                zip_ref = zipfile.ZipFile(file_path, 'r')
                zip_ref.extractall(dir_path)
                zip_ref.close()
                os.remove(file_path)
            else:
                (name, header) = urllib.request.urlretrieve(resource['resource_data_url'], file_path)
            
            print("download file %d" %(index))
            index += 1

        print('done download')
        return 'done'



    def findByDatasetIds(self, dataset_id):
        req = None

        self.payload = {'dataset_ids__in': [dataset_id]}
        req = requests.post(API_URL + '/find', headers = HEADERS, data = json.dumps(self.payload))
        response = req.json()
        
        if isinstance(response, dict) and 'error' in response:
            print(response['error'])
            return 'error'
        
        return response['resources']


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