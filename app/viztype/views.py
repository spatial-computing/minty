from flask import jsonify, request, url_for, redirect, current_app, render_template, flash, make_response
from flask.views import MethodView

import pymongo

class VizType(MethodView):
    def __init__(self):
        self.mongo_client = pymongo.MongoClient(current_app.config['MONGODB_DATABASE_URI'])
        self.mongo_db = self.mongo_client["mintcast"]
        self.mongo_viz = self.mongo_db["viztype"]
        self.pipeline = [
            {"$match": {
                "type" : "viz-type"
                }
            },
            {"$lookup": { 
                "from": "viztype", 
                "localField":"name", 
                "foreignField": "belongto", 
                "as": "metadata"
                }
            }
        ]
    def get(self):
        return render_template('viztype/index.html', viztype=list(self.mongo_viz.aggregate(self.pipeline)))

    def post(self):
        pass