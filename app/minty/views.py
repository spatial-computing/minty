from flask import jsonify, request, url_for, redirect, current_app, render_template, flash, make_response
from flask.views import MethodView
# from .. import app
import pymongo
from app.dcwrapper import api

class LayerJson(MethodView):
    def __init__(self):
        self.mongo_client = pymongo.MongoClient(current_app.config['MONGODB_DATABASE_URI'])
        self.mongo_db = self.mongo_client["mintcast"]
        self.mongo_col = self.mongo_db["layer"]

    def get(self, md5):
        jsonData = self.mongo_col.find_one({'$or': [{'md5vector': md5}, {'dcid': md5}]})
        
        if jsonData:
            del jsonData['_id']
            return jsonify(jsonData)
        else:
            return "{ }"
    def __del__(self):
        self.mongo_client.close()

class HasLayerJson(MethodView):
    def __init__(self):
        self.mongo_client = pymongo.MongoClient(current_app.config['MONGODB_DATABASE_URI'])
        self.mongo_db = self.mongo_client["mintcast"]
        self.mongo_col = self.mongo_db["layer"]

    def get(self, md5):
        jsonData = self.mongo_col.find_one({'$or': [{'md5vector': md5}, {'dcid': md5}]}, {'_id':False})
        
        if jsonData:
            return jsonify({'has': True})
        else:
            return jsonify({'has': False})
    def __del__(self):
        self.mongo_client.close()
class DcidJson(MethodView):
    def __init__(self):
        self.mongo_client = pymongo.MongoClient(current_app.config['MONGODB_DATABASE_URI'])
        self.mongo_db = self.mongo_client["mintcast"]
        self.mongo_col = self.mongo_db["layer"]
    def get(self, dcid):
        jsonData = self.mongo_col.find_one({'dcid': dcid})
        
        if jsonData:
            del jsonData['_id']
            return jsonify(jsonData)
        else:
            return "{ }"
    def __del__(self):
        self.mongo_client.close()
           
class MetadataJson(MethodView):
    def __init__(self):
        self.mongo_client = pymongo.MongoClient(current_app.config['MONGODB_DATABASE_URI'])
        self.mongo_db = self.mongo_client["mintcast"]
        self.mongo_col = self.mongo_db["metadata"]

    def get(self):
        jsonData = self.mongo_col.find_one({'type': 'mintmap-metadata'})
        
        # print(jsonData, type(jsonData['_id']))
        if jsonData:
            del jsonData['_id']
            return jsonify(jsonData)
        else:
            return "{ }"
    def __del__(self):
        self.mongo_client.close()
        
class AutocompleteJson(MethodView):
    def __init__(self):
        self.mongo_client = pymongo.MongoClient(current_app.config['MONGODB_DATABASE_URI'])
        self.mongo_db = self.mongo_client["mintcast"]
        self.mongo_col = self.mongo_db["metadata"]

    def get(self):
        jsonData = self.mongo_col.find_one({'type': 'mintmap-autocomplete'})
        
        # print(jsonData, type(jsonData['_id']))
        if jsonData:
            del jsonData['_id']
            del jsonData['type']
            return jsonify(jsonData)
        else:
            return "{ }"
    def __del__(self):
        self.mongo_client.close()
        
class VisualizeAction(MethodView):
    def __init__(self):
        self.msg = {
            200: 'Task is establised on the server.',            
            404.4: 'Metadata or Dataset (type 4) is not avaliable',
            404.3: 'Metadata or Dataset (type 3) is not avaliable',
            404.2: 'Metadata or Dataset (type 2) is not avaliable.',
            404.1: 'Dataset has no variable',
            404: 'Viz_config not found in dataset',
            301: 'File is being downloaded',
            415: 'Unsupported visulaization type',
            500: 'Internal or metadata Error',
            400: 'Bad request, please send dataset_id and data_url',
            400.1: 'Bad request, viz_config does not include a uuid'
        }

    def get(self, dataset_id):
        if dataset_id == 'dataset':
            print(request.args)
            if 'dataset_id' not in request.args or 'data_url' not in request.args:
                return jsonify({"status": 400, "msg": self.msg[status]})
            dataset_id = request.args['dataset_id']
            data_url = request.args['data_url']
            viz_config = None
            # http://52.90.74.236:65533/minty/visualize/dataset?dataset_id=<>&viz_config_id=viz_config_<uuid2>&data_url=<>
            # viz_config_id=viz_config_<uuid2>&data_url=<>
            if 'viz_config' in request.args:
                viz_config = request.args['viz_config']
            # /visualize/dataset?dataset_id=<>&data_url=<>
            getdata = api.DCWrapper(bash_autorun=True)
            status = getdata.findByDatasetId(dataset_id, data_url=data_url, viz_config=viz_config) # job.status
            return jsonify({"dataset_id": dataset_id, "status": status, "msg": self.msg[status]})
        else:
        
            #    job = start a DCWrapper with dataset_id
            getdata = api.DCWrapper(bash_autorun=True)
            status = getdata.findByDatasetId(dataset_id) # job.status
            return jsonify({"dataset_id": dataset_id, "status": status, "msg": self.msg[status]})
      
class VizType(MethodView):
    def __init__(self):
        self.mongo_client = pymongo.MongoClient(current_app.config['MONGODB_DATABASE_URI'])
        self.mongo_db = self.mongo_client["mintcast"]
        self.mongo_viz = self.mongo_db["viztype"]
        self.pipeline = [
            {
                "$match": {
                    "type" : "type"
                }
            },
            {
                "$lookup": { 
                    "from": "viztype", 
                    "localField":"name", 
                    "foreignField": "belongto", 
                    "as": "metadata"
                }
            },
            {
                "$project": {
                    "metadata._id": 0,
                    "_id": 0,
                    "type": 0,
                    "metadata.type": 0
                }
            }
        ]

    def get(self):
        ret = {
            "types":[]
        }
        for ele in self.mongo_viz.aggregate(self.pipeline):
            ret["types"].append(ele["name"])
            ret[ele["name"]] = {
                "keys":[]
            }
            for m in ele["metadata"]:
                ret[ele["name"]]["keys"].append(m["name"])
                key_name = m["name"]
                del m["name"]
                ret[ele["name"]][key_name] = m
        
        return jsonify(ret)
    def __del__(self):
        self.mongo_client.close()
        


class ChartData(MethodView):
    def __init__(self):
        self.mongo_client = pymongo.MongoClient(current_app.config['MONGODB_DATABASE_URI'])
        self.mongo_db = self.mongo_client["mintcast"]
        self.mongo_chart = self.mongo_db["chart"]
    def get(self, dataset_id):
        ret = self.mongo_chart.find_one({"dataset_id" : dataset_id}, {"_id": False})
        if ret:
            return jsonify(dict(ret))
        else:
            return jsonify({'status': 404})
    def __del__(self):
        self.mongo_client.close()

class TileStacheIndex(MethodView):
    def get(self):
        return render_template('minty/tilestache_index.html')

class TileStacheConfig(MethodView):
    def __init__(self):
        self.mongo_client = pymongo.MongoClient(current_app.config['MONGODB_DATABASE_URI'])
        self.mongo_db = self.mongo_client["mintcast"]
        self.mongo_metadata = self.mongo_db["metadata"]
    
    def get(self):
        ret = self.mongo_metadata.find_one({"type" : "tilestache-config"}, {"_id": False, "type": False})
        if ret:
            return jsonify(dict(ret))
        else:
            return jsonify({})

    def __del__(self):
        self.mongo_client.close()
  


