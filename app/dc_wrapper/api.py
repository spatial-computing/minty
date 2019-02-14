import requests
import json
import os
import magic
from datetime import timedelta

from app.models import db, DataSet, Bash
from app.jobs import rq_instance, rq_download_job, rq_run_command_job, rq_create_bash_job, rq_check_job_status_scheduler
from app.bash import bash_helper
from rq import Connection, Worker, Queue
from rq.utils import parse_timeout


HEADERS = {'Content-Type': 'application/json', 'cache-control': 'no-cache', 'Postman-Token': '3084e843-b082-4bfb-be1a-bb4ac72c865'}
API_URL = 'http://api.mint-data-catalog.org/datasets'
API_STANDARD_NAME = API_URL + '/dataset_standard_variables'
API_FIND_RESOURCES = API_URL + '/find'
API_FIND_DATASETS = 'http://api.mint-data-catalog.org/find_datasets'
API_UPDATE_VIZUALIZE_STATUS = 'http://api.mint-data-catalog.org/datasets/update_dataset_viz_config'
API_REGISTER_DATASET = 'https://api.mint-data-catalog.org/datasets/register_datasets'

PROVENANCE_ID = 'cacc9aa2-f532-42e6-8302-45db8684ef7a'

# Scheduler
RQ_SCHEDULER_START_IN_SECONDS = 5
RQ_SCHEDULER_REPEAT_TIMES = parse_timeout('1d') / 60  # Repeat this number of times (None means repeat forever)
RQ_SCHEDULER_INTERVAL = 5

SINGLE_FILE_TAG = 'single file tag'
class dc_wrapper(object):
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

    def find_by_dataset_id(self, dataset_id, data_url=None, viz_config=None):
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

        dataset = self.find_dataset_by_id(dataset_id)
        if dataset == 'error':
            status = 404.2
            return status
        resources = None
        if not data_url:
            resources = self.find_resources_by_id(dataset_id)
            if resources == 'error':
                status = 404.3
                return status
        else:
            resources = data_url

        the_first_viz_config = None
        if not viz_config:
            arr = []
            for k, v in dataset['dataset_metadata'].items():
                if k.startswith('viz_config'):
                    arr.append(k)
            if len(arr) == 0:
                status = 404.4
                return status
            arr.sort()
            the_first_viz_config = arr[0]
        else:
            the_first_viz_config = viz_config

        #print(arr)
        if the_first_viz_config not in dataset['dataset_metadata']:
            status = 404
            return status
        metadata = dataset['dataset_metadata'][the_first_viz_config]

    # "mint-chart", 
    # "mint-map", 
    # "mint-map-time-series"
        uuid2 = the_first_viz_config[len('viz_config_'):]
        if len(uuid2) < 2:
            status = 400.1
            return status
        command_args = {
            "layer_name": metadata['metadata']['title'].strip().replace(' ', '-_-').replace('\t','-_-'),
            "viz_config": the_first_viz_config,
            "viz_type": metadata['viz_type'],
            "md5vector": uuid2,
            "dataset_id": dataset['dataset_id']
        }
        if data_url:
            command_args.update({"data_url": data_url})

        if metadata['viz_type'] != 'mint-chart':
            command_args.update({
                "file_type": metadata['metadata']['file-type'],
            })
        else:
            # Bar Dot Donut
            command_args.update({
                "chart_type": metadata['metadata']['chart-type'].lower(),
                "file_type": 'csv',
                "type": 'csv'
            })
        # Black2White BuPu YlGnBl
        # South Sudan Pongo Basin No Clip
        if 'shapefile' in metadata['metadata']:
            if metadata['metadata']['shapefile'] == "South Sudan":
                command_args["with_shape_file"] = "shp/ss.shp"
            elif metadata['metadata']['shapefile'] == "Pongo Basin":
                command_args["with_shape_file"] = "shp/WBD.shp"
            elif metadata['metadata']['shapefile'] == "Gel-Aliab":
                command_args["with_shape_file"] = "shp/GelAliab.shp"
        
        if 'color-map' in metadata['metadata']:
            command_args["load_colormap"] = "shp/colortable.txt"
            if metadata['metadata']['color-map'] == "Black2White":
                command_args["load_colormap"] = "shp/colortable.txt"
            elif metadata['metadata']['color-map'] == "BuPu":
                command_args["load_colormap"] = "shp/bupu_colormap.txt"
            elif metadata['metadata']['color-map'] == "YlGnBl":
                command_args["load_colormap"] = "shp/ylgnbl_colormap.txt"

        if 'file-type' in metadata['metadata']:
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
                    command_args['type'] = 'tiff' # use start time to detect whether is timeseries
            elif metadata['metadata']['file-type'] == 'csv':
                    command_args['type'] = 'csv'
        #metadata['viz_type'] = 'abc'
        if metadata['viz_type'] == 'mint-map-time-series':
            command_args.update({
                "output_dir_structure": metadata['metadata']['directory-structure'] + '/*.mbtiles',
                "directory_structure":metadata['metadata']['directory-structure'],
                "start_time": metadata['metadata']['start-time'],
                "end_time": metadata['metadata']['end-time'],
                "datatime_format": metadata['metadata']['datatime-format'],
                "dir": self.download_dist + '/' + uuid2,
            })
        else:
            # if (not isinstance(resources, str)) and (len(resources) == 1):
            command_args['data_file_path'] = SINGLE_FILE_TAG
        #print(command_args)
        self.command_args = command_args

        download_status = self._download(resources, uuid2, **command_args)
        if download_status == 'done_queue':
            status = 200
        else:
            status = 500

        return status
        
    def find_resources_by_id(self, dataset_id):
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

    def find_dataset_by_id(self, dataset_id):
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

    def get_dataset_info_convert_to_register_info(self, dataset_id, viz_config):
        dataset_info = self.find_dataset_by_id(dataset_id)
        if dataset_info == 'error':
            return 'error'

        register_info = {
            "record_id" : dataset_info['dataset_id'],
            "description": dataset_info['dataset_description'],
            "name": dataset_info['dataset_name'],
            "metadata": {
                viz_config: dataset_info['dataset_metadata'][viz_config]
            }
        }
        return register_info

    def register_to_dc(self, payload):
        # curl -vX POST  -d @/Users/liber/Downloads/fake_dataset/wtf_flood.json --header "Content-Type: application/json" --header 'X-Api-Key: mint-data-catalog:7d421ed6-f8dd-456f-93ad-8890d8194ff1:c2ad60ce-11bf-482e-8268-ea5973eae102'
        # print(payload, type(payload))
        payload["provenance_id"] = PROVENANCE_ID
        payload = {"datasets": [
                payload
            ]
        }
        req = requests.post(API_REGISTER_DATASET, headers=HEADERS, data=json.dumps(payload))
        print(json.dumps(payload))
        if req.status_code != 200:
            return 'error'
        
        response = req.json()
        if not isinstance(response, dict):
            return 'error'

        if 'error' in response:
            print(response['error'])
            return 'error'

        if 'result' not in response:
            return 'error'
        
        if response['result'] != 'success':
            return 'error'
        
        if len(response['datasets']) == 0:
            return 'error'

        return response['datasets'][0]


    def _download(self, resource_list, uuid2, **command_args):
        #print(len(resource_list))
        #print(os.getcwd())
        dir_path = self.download_dist + '/' + uuid2
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)
        jobs = []
        download_id_text = ''
        if isinstance(resource_list, str):
            _j = rq_download_job.queue(resource_list, uuid2, 0, dir_path)
            jobs.append(_j.id)
            download_id_text += _j.id
            self.command_args['rqids'] = _j.id
        else:
            for index, resource in enumerate(resource_list):
                _j = rq_download_job.queue(resource, uuid2, index, dir_path)
                jobs.append(_j.id)
                download_id_text = download_id_text + ',' + _j.id 
                self.command_args['rqids'] = _j.id
        
        download_id_text = download_id_text.lstrip(',')
        self.command_args['download_ids'] = download_id_text

        self.command_args['status'] = 'downloading'
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
        
        bash = self._buildBash(db.session, from_download_func=True, **self.command_args)
        # bash_create_job = rq_create_bash_job.queue(self, **command_args)
        print('done download enqueue')
        return 'done_queue'

    def _buildBash(self, db_session, from_download_func=False, **kwargs):
        bash_check = db_session.query(Bash).filter_by(md5vector=kwargs['md5vector']).first()

        if not from_download_func and bash_check and 'data_file_path' in kwargs and kwargs['data_file_path'] == SINGLE_FILE_TAG:
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
        print('kepia###3', self.command_args['status'])
        if self.command_args['status'] == 'running' or self.command_args['status'] == 'ready_to_run':
            return
        
        from app.models import get_db_session_instance
        db_session = get_db_session_instance()
        if not self.bash_autorun:
            self.command_args['status'] = 'ready_to_run'
        else:
            self.command_args['status'] = 'running'
        
        bash = self._buildBash(db_session, from_download_func=False, **self.command_args)
        if self.bash_autorun:
            bash = db_session.query(Bash).filter_by(md5vector=bash.md5vector).first()
            
            command = bash_helper.find_command_by_id(bash.id, db_session=db_session)
            from app.job import queue_job_with_connection
            from redis import Redis
            
            # Make sure mint-chart be processed first rather than wait in line with mint-map*
            queue_name = None
            if bash.viz_type == 'mint-chart':
                queue_name = 'high'

            rq_connection = Redis.from_url(redis_url)
            bash_job = queue_job_with_connection(
                rq_run_command_job, 
                rq_connection,
                command, 
                bash.id,
                redis_url,
                _queue_name=queue_name
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
                    suffix = self._check_suffix(filename)
                    for mgx in FILE_TYPE_TO_MAGIC[file_type.lower()]:
                        if fm.startswith(mgx) and suffix in FILE_TYPE_TO_SUFFIX[file_type.lower()]:
                            return filename
                    # check type
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
    
    def unregister_dataset_visualize_status(self, dataset_id, viz_config, option):
        payload = {
                'dataset_id': dataset_id, 
                'viz_config_id': viz_config,
                '$set': {
                        'visualized' : option
                    }
                }
        print(dataset_id)
        print(viz_config)
        req = requests.post(API_UPDATE_VIZUALIZE_STATUS, data = json.dumps(payload))
        if req.status_code != 200:
            return 'error'
        
        response = req.json()
        print(response)
        if not isinstance(response, dict):
            return 'error'

        if 'error' in response:
            print(response['error'])
            return 'error'

        return 'success'
