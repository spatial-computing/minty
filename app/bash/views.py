from flask import jsonify, request, url_for, redirect, current_app, render_template, flash, make_response
from flask.views import MethodView

import pymongo
from .bash_helper import get_bash_column_metadata, find_bash_attr, delete_bash, add_bash, find_bash_by_id, update_bash, find_all, find_one, run_bash, find_command_by_id
import os

import json
from app.job import rq_instance
from app.dcwrapper import api

import ast
KEY_FILTER_FOR_USER = {'_sa_instance_state',  'id', 'viz_type'}
class DeleteBash(MethodView):

    def get(self, bash_id):
        delete_bash(bash_id)
        return redirect(url_for('bash.bash_list'))

class AddBash(MethodView):
    def get(self):
        headers = {'Content-Type': 'text/html'}
        bash = get_bash_column_metadata()
        print(bash)
        txt = []
        boolean = []
        for key in bash:
            if(key not in KEY_FILTER_FOR_USER):
                if bash[key] == type(True):
                    boolean.append(key)
                else:
                    txt.append(key)
        txt.sort()
        boolean.sort()
        return make_response(render_template('bash/bash.html',txt = txt,boolean = boolean,bash = {}),200,headers)
 
    def post(self):
        headers = {'Content-Type': 'text/html'}
        result = request.form
        newbash = {}
        for key in result:
            if result[key]=='on':
                newbash[key]=True
            else:
                newbash[key]=result[key]

        # add command to new added bash
        newbash.pop('csrf_token', None)
        if newbash['command']=='':
            newbash['command']=combine(newbash)
        add_bash(**newbash)
     
        return url_for('bash.bash_list')


class EditBash(MethodView):
    def get(self,bash_id = None):
        headers = {'Content-Type': 'text/html'}
        if bash_id is None:
            return make_response('No record', 404)
        else:
            bash = find_bash_by_id(bash_id)
            if not bash:
                return make_response('No record', 404)
            bash = bash._asdict()
            txt = []
            boolean = []
            for key in bash:
                if(key not in KEY_FILTER_FOR_USER):
                    if type(bash[key]) == type(True):
                        boolean.append(key)
                    else:
                        txt.append(key)
            txt.sort()
            boolean.sort()
            return make_response(render_template('bash/bash.html',txt = txt,boolean = boolean,bash = bash),200,headers)
# infact it is a put method to update the bash

    def post(self,bash_id):
        headers = {'Content-Type': 'text/html'}
        result = request.form
        newbash = {}
        for key in result:
            if key != 'csrf_token':
                if result[key]=='on':
                    newbash[key]=True
                else:
                    newbash[key]=result[key]
        update_bash(bash_id, **newbash)
       
        return url_for('bash.bash_list')
        #return make_response(render_template('bash/bashres.html',res = newbash),200,headers)

class BashList(MethodView):

    def __init__(self):
        self.mongo_client = pymongo.MongoClient(current_app.config['MONGODB_DATABASE_URI'])
        self.mongo_db = self.mongo_client["mintcast"]
        self.mongo_mintcast_default = self.mongo_db["metadata"]
        self.default_setting = self.mongo_mintcast_default.find_one({'type': 'minty-mintcast-task-dashboard-default-value-setting'}, {"_id": False,"type":False})	

    def get(self):
        bashes = find_all(limit=20, page=0)
        res = []
        ids = []
        for bash in bashes:
            bash = bash._asdict()
            
            # bash['command'] = find_command_by_id(bash['id'])
            res.append(bash)
            ids.append(str(bash['id']))
        th = []
        # for key in vars(bashes[0]):
        #     if(key != "_sa_instance_state"):
        #         th.append(key)
        th.append("command")
        th.sort()
        headers = {'Content-Type': 'text/html'}

        # return make_response(render_template('bash/bashList.html',th = th,res = res,ids = ids, default_setting=self.default_setting),200,headers)
        return make_response(
            render_template(
                'bash/bashList.html', 
                th=th, 
                res=res,
                default_setting=self.default_setting,
                ids = ids), 200, headers)

    def post(self):
        para = request.form
        bash_ids = para['bash_ids']
        setting={"dev_mode_off":False,"disable_new_res":False,"scp_to_default_server":False}
        for key in para:
            if para[key] =='on':
                setting[key] = True
        bash_ids = ast.literal_eval(bash_ids)
        for bash_id in bash_ids:
            update_bash(bash_id,**setting)
        return jsonify({"status": "success"})

class Run(MethodView):
    def post(self):
        bashid = request.form["bashid"]
        bash = find_bash_by_id(bashid)
        if not bash:
            return jsonify({"status": "No record"})
        bash = bash._asdict()

        if (bash['data_file_path'] == '' and os.path.exists(bash['dir'])) or (os.path.isfile(bash['data_file_path'])):
            run_bash(bashid)
        else:
            # r = requests.get(url_for('minty.visualize_action', dataset_id=bash['md5vector']))
            getdata = api.DCWrapper()
            status = getdata.findByDatasetId(bash['md5vector']) # job.status
        return jsonify({"status": "queued"})

class Status(MethodView):
    def post(self):
        if 'type' in request.form and request.form['type'] == 'batch':
            bash_ids = list(map(int, filter(lambda x: x  !=  '',request.form['bashid'].split(',') ) ))
            job_ids = request.form['jobid'].split(',')
            status = []
            for idx, job_id in enumerate(job_ids):
                no_exception, job = rq_instance.job_fetch(job_id)
                if no_exception:
                    _s = job.get_status()
                    status.append(_s if _s else '')
                else:
                    _s = find_bash_attr(bash_ids[idx],'status')
                    status.append(_s if _s else '')
                   
            return jsonify({ "status": status })
        else:
            bash_id = request.form['bashid']
            job_id = request.form['jobid']
            # print(jobid)
            status = ''
            logs = {}

            no_exception, job = rq_instance.job_fetch(job_id)
            if no_exception:
                status = job.get_status()
                if job.result:
                    logs = json.loads(job.result)
                else:
                    logs = {'output': 'No stdout', 'error': 'No stderr'}
                if job.exc_info:
                    logs['exc_info'] = job.exc_info
                else:
                    logs_tmp_var = json.loads(find_bash_attr(bash_id,'logs'))
                    logs['exc_info'] = logs_tmp_var['exc_info']
            else:
                status = find_bash_attr(bash_id,'status')
                logs = json.loads(find_bash_attr(bash_id,'logs'))
            
            status = status if status else ''
            if not logs:
                logs = {'output':'', 'error':'', 'exc_info':''}

            return jsonify({
                "status": status, 
                "logs": logs
                })


class MIntcastTaskDefaultSetting(MethodView):
    def __init__(self):
        self.mongo_client = pymongo.MongoClient(current_app.config['MONGODB_DATABASE_URI'])
        self.mongo_db = self.mongo_client["mintcast"]
        self.mongo_mintcast_default = self.mongo_db["metadata"]

    def get(self):
        ret = self.mongo_mintcast_default.find_one({'type': 'minty-mintcast-task-dashboard-default-value-setting'}, {"_id": False})
        if ret:
            return jsonify(dict(ret))
        else:
            return jsonify({'status': 404})

    def post(self):
        name = request.form['name']
        status = request.form['status']
        setting = {name:status}
        self.mongo_mintcast_default.update_one(
            {"type":"minty-mintcast-task-dashboard-default-value-setting"},
            {'$set':setting},
            upsert=True

        )
        return jsonify({"status": "ok","name":name,"status":status})

    def __del__(self):
        self.mongo_client.close()
