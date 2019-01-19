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
                "type" : "type"
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
        return render_template('viztype/index.html', viztypes=list(self.mongo_viz.aggregate(self.pipeline)))

    def post(self):
        if not request.form["value"]:
            return jsonify({"status": "err"})
        if request.form["type"] == "add":
            if request.form["format"] == "type":
                ftmp = self.mongo_viz.find_one({"type":"type","name":request.form["value"]})
                if not ftmp:
                    self.mongo_viz.insert_one({"type":"type", "name":request.form["value"]})
            else:
                ftmp = self.mongo_viz.find_one({"type":"key","name":request.form["value"], "belongto": request.form["type_name"]})
                if not ftmp:
                    self.mongo_viz.insert_one({
                        "type": "key", 
                        "name":request.form["value"],
                        "placeholder": request.form["placeholder"],
                        "htmltag": request.form["htmltag"],
                        "belongto": request.form["type_name"],
                        "options": request.form["options"],
                        "description": request.form["description"]
                    })
        else:
            if request.form["format"] == "type":
                ftmp = self.mongo_viz.find_one({
                    "type":"type",
                    "name":request.form["former"]
                    })
                if ftmp:
                    self.mongo_viz.update_one({
                        "type":"type", 
                        "name":request.form["former"]
                        }, 
                        { 
                        '$set': { "name":request.form["value"] }
                        }
                    )
            else:
                ftmp = self.mongo_viz.find_one({
                    "type": "key",
                    "name": request.form["former"],
                    "belongto": request.form["type_name"]
                    })
                if ftmp:
                    self.mongo_viz.update_one({
                        "type": "key", 
                        "name": request.form["former"],
                        "belongto": request.form["type_name"]
                        }, 
                        { 
                        '$set': {
                                    "name": request.form["value"],
                                    "placeholder": request.form["placeholder"],
                                    "htmltag": request.form["htmltag"],
                                    "options": request.form["options"],
                                    "description": request.form["description"]
                                }
                        }
                    )
        # print(request.form)
        return jsonify({"status": "ok"})
    def delete(self):
        if request.form["type"] == "key":
            self.mongo_viz.delete_one({
                "type":"key",
                "name":request.form["name"],
                "belongto": request.form["belongto"]
                })
        else:
            self.mongo_viz.delete_many({
                "type":"key",
                "belongto": request.form["name"]
                })
            self.mongo_viz.delete_many({
                "type":"type",
                "name": request.form["name"]
                })
        return jsonify({"status": "ok"})

