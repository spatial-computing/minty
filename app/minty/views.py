from flask import jsonify, request, url_for, redirect, current_app, render_template, flash, make_response
from flask.views import MethodView
# from .. import app
import pymongo
    
class LayerJson(MethodView):
    def __init__(self):
        self.mongo_client = pymongo.MongoClient(current_app.config['MONGODB_DATABASE_URI'])
        self.mongo_db = self.mongo_client["mintcast"]
        self.mongo_col = self.mongo_db["layer"]

    def get(self, md5):
        jsonData = self.mongo_col.find_one({'md5vector': md5})
        self.mongo_client.close()
        if jsonData:
            del jsonData['_id']
            return jsonify(jsonData)
        else:
            return "{ }"

class DcidJson(MethodView):
    def __init__(self):
        self.mongo_client = pymongo.MongoClient(current_app.config['MONGODB_DATABASE_URI'])
        self.mongo_db = self.mongo_client["mintcast"]
        self.mongo_col = self.mongo_db["layer"]
    def get(self, dcid):
        jsonData = self.mongo_col.find_one({'dcid': int(dcid)})
        self.mongo_client.close()
        if jsonData:
            del jsonData['_id']
            return jsonify(jsonData)
        else:
            return "{ }"
              
class MetadataJson(MethodView):
    def __init__(self):
        self.mongo_client = pymongo.MongoClient(current_app.config['MONGODB_DATABASE_URI'])
        self.mongo_db = self.mongo_client["mintcast"]
        self.mongo_col = self.mongo_db["metadata"]

    def get(self):
        jsonData = self.mongo_col.find_one({'type': 'mintmap-metadata'})
        self.mongo_client.close()
        # print(jsonData, type(jsonData['_id']))
        if jsonData:
            del jsonData['_id']
            return jsonify(jsonData)
        else:
            return "{ }"

class AutocompleteJson(MethodView):
    def __init__(self):
        self.mongo_client = pymongo.MongoClient(current_app.config['MONGODB_DATABASE_URI'])
        self.mongo_db = self.mongo_client["mintcast"]
        self.mongo_col = self.mongo_db["metadata"]

    def get(self):
        jsonData = self.mongo_col.find_one({'type': 'mintmap-autocomplete'})
        self.mongo_client.close()
        # print(jsonData, type(jsonData['_id']))
        if jsonData:
            del jsonData['_id']
            del jsonData['type']
            return jsonify(jsonData)
        else:
            return "{ }"

class VisualizeAction(MethodView):
    def __init__(self):
        self.msg = {
            200: 'Task is establised on the server.',            
            404: 'Metadata or Dataset is not avaliable',
            415: 'Unsupported visulaization type',
            500: 'Internal or metadata Error'
        }

    def get(self, dataset_id):
        # TODO: to Shawn
        #    job = start a DCWrapper with dataset_id
        status = 200 # job.status
        return "{\"dataset_id\": \"%s\", \"status\": %s, \"msg\": \"%s\"}" \
                % (dataset_id, status, self.msg[status])
        # return "{testmsg: 'working on %s'}" % (dataset_id)

class VizType(MethodView):
    def __init__(self):
        pass

    def get(self):
        pass