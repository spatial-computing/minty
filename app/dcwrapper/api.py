import requests
from rq import *
from redis import Redis
import time
import json
import os 
import wget
import zipfile
from app.models import db


HEADERS = {'Content-Type': 'application/json', 'X-Api-Key': 'mint-data-catalog:e038e64c-c950-4fbc-9070-a3e7138b6c4f:dce8a09a-200e-43ca-b996-810c2c437d3a', 'cache-control': 'no-cache', }
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
            self.status = 500
            return self.status

        #db
        print(response['dataset'])
        
        #dowload
        redis_conn = Redis()
        q = Queue(connection=redis_conn)  # no args implies the default queue
        job = q.enqueue(self._download, dataset_id)
        print(job.id)
        print(job.status)

        if job.status == 'queued':
            self.status = 200
        else:
            self.status == 404
        
        return self.status

    def _download(self, dataset_id):
        data = self.findByDatasetIds(dataset_id)
        #if data == 'error'
        print(data)
        print(os.getcwd())
        if os.path.exists(os.getcwd() + '/app/static/dowloads/' + dataset_id):
            return 'file_exists'

        is_zip = False
        if data[0]['resource_metadata'].get('is_zip') is not None:
            if data[0]['resource_metadata']['is_zip'] == 'true':
                is_zip = True

        file = data[0]['resource_data_url'].split('/')
        file_name = file[len(file) - 1]
        dir_path = os.getcwd() + '/app/static/dowloads/' + dataset_id
        os.mkdir(dir_path)
        file_path = dir_path + '/' + file_name

        if is_zip:
            wget.download(data[0]['resource_data_url'], file_path)
            zip_ref = zipfile.ZipFile(file_path, 'r')
            zip_ref.extractall(dir_path)
            zip_ref.close()
            os.remove(file_path)
        else:
            wget.download(data[0]['resource_data_url'], file_path)

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