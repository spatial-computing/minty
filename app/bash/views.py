from flask import jsonify, request, url_for, redirect, current_app, render_template, flash, make_response
from flask.views import MethodView

import pymongo
from .bash_helper import find_bash_by_id_for_run, get_bash_column_metadata, find_bash_attr, delete_bash, add_bash, find_bash_by_id, update_bash, find_all, find_one, run_bash, find_command_by_id, combine, find_count,find_bash_attrs
import os
import math
import json
from app.job import rq_instance
from app.dcwrapper import api

import ast
KEY_FILTER_FOR_USER = {'_sa_instance_state',  'id', 'viz_type'}
MINTY_URL = 'http://minty.mintviz.org/'
CHECK_JOB_ALL_IDS = ['download_ids','rqids','after_run_ids']
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
        self.mongo_mintcast_default_controller = self.mongo_db["metadata"]
        self.default_setting = self.mongo_mintcast_default.find_one({'type': 'minty-mintcast-cmd-parameter-setting'}, {"_id": False,"type":False})
        self.default_setting_controller = self.mongo_mintcast_default_controller.find_one({'type': 'minty-dashboard-setting'}, {"_id": False,"type":False})	
    
    def _safe_cast_int(self, s, default_value=0):
        try:
            return int(s)
        except Exception as e:
            return default_value

    def get(self):
        page = 1
        default_limit = 8
        limit = default_limit
        if 'page' in request.args:
            page = self._safe_cast_int(request.args['page'], default_value=page)
        if 'limit' in request.args:
            limit = self._safe_cast_int(request.args['limit'], default_value=limit)
        if page < 1:
            page = 1
        if limit < 2 or limit > 20:
            limit = default_limit
        total_records = find_count()
        total_page_num = math.ceil(total_records / limit);
        if page > total_page_num:
            page = total_page_num

        bashes = find_all(limit=limit, page=page-1)
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

        return make_response(
            render_template(
                'bash/bashList.html', 
                th=th, 
                res=res,
                default_setting=self.default_setting,
                default_setting_controller=self.default_setting_controller,
                total_page_num=total_page_num,
                current_page=page,
                current_limit=limit,
                default_limit=default_limit,
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

class Cancel(MethodView):
    def post(self):
        bashid = request.form['bashid']
        bash_job_id = find_bash_attr(bashid,"rqids")

        # check status running
        if not bash_job_id:
            update_bash(bashid, status="ready_to_run")
            return jsonify({"status":"No bash job id"})
        no_exception, job = rq_instance.job_fetch(bash_job_id)
        if no_exception:
            job.cancel()
            update_bash(bashid, status="ready_to_run") 
            return jsonify({"status":"Job cancelled"})
        else:
            update_bash(bashid, status="ready_to_run")
        return jsonify({"status":"No such job"})


class Run(MethodView):
    def post(self):
        bashid = request.form["bashid"]
        bash = find_bash_by_id_for_run(bashid)
        if not bash:
            return jsonify({"status": "No record"})
        bash = bash._asdict()
        print(bash)
        if bash['status'] in {'running', 'downloading', 'started'}:
            return jsonify({"status": "It\'s running"})

        if (bash['data_file_path'] == '' and os.path.exists(bash['dir'])) or (os.path.isfile(bash['data_file_path'])):
            run_bash(bashid)
            print(bashid)
            update_bash(bashid, status="running")
        else:
            getdata = api.DCWrapper()
            status = getdata.findByDatasetId(bash['dataset_id'], data_url=bash['data_url'], viz_config=bash['viz_config']) 
        return jsonify({"status": "queued"})

class Unregister(MethodView):
    def post(self):
        dataset_id = request.form['dataset_id']
        viz_config = request.form['viz_config']
        option = request.form['option']
        unregister_dc = api.DCWrapper()
        status = unregister_dc.unregister_dataset_visualize_status(dataset_id, viz_config, option)
        return jsonify({"status":status})

class Status(MethodView):
    def post(self):
        if 'type' in request.form and request.form['type'] == 'batch':
            bash_ids = list(map(int, filter(lambda x: x  !=  '',request.form['bashid'].split(',') ) ))
            job_ids = request.form['jobid'].split(',')
            status = []
            for idx, job_id in enumerate(job_ids):
                _s = ''
                all_ids = find_bash_attrs(bash_ids[idx],CHECK_JOB_ALL_IDS)
                for job_id in all_ids:
                    no_exception, job = rq_instance.job_fetch(job_id)
                    if no_exception and job.get_status() == 'failed':
                        _s = 'failed'
                        break
                if _s != 'failed':
                    _s = find_bash_attr(bash_ids[idx],'status')
                status.append(_s if _s else '')

                # no_exception, job = rq_instance.job_fetch(job_id)
                # _s = ''
                # if no_exception:
                #     _s = job.get_status()
                # if _s != 'failed':
                #     _s = find_bash_attr(bash_ids[idx],'status')
                # status.append(_s if _s else '')
            
            return jsonify({ "status": status })
        else:
            bash_id = request.form['bashid']
            job_id = request.form['jobid']
            download_id = request.form['download_id']
            after_run_ids = request.form['after_run_ids']
            all_ids = [job_id,download_id,after_run_ids]
            status = 'not_found'
            logs = {}
            # get job status 
            for job_id in all_ids:
                print(job_id)
                no_exception, job = rq_instance.job_fetch(job_id)
                if no_exception and job.get_status() == 'failed':
                    status = 'failed'
                    break
            if status != 'failed':
                status = find_bash_attr(bash_id,'status')
            else:
                substatus = find_bash_attr(bash_id,'status')
                if substatus != 'failed':
                    update_bash(bash_id, status="failed")


            no_exception, job = rq_instance.job_fetch(job_id)
            if no_exception:
                # status = job.get_status()
                # if status != 'failed':
                #     status = find_bash_attr(bash_id,'status')
                # else:
                #     substatus = find_bash_attr(bash_id,'status')
                #     if substatus != 'failed':
                #         update_bash(bash_id, status="failed")

                if job.result:
                    logs = json.loads(job.result)
                else:
                    logs = {'output': 'No stdout', 'error': 'No stderr'}
                if job.exc_info:
                    logs['exc_info'] = job.exc_info
                else:
                    logs_tmp_var = json.loads(find_bash_attr(bash_id,'logs'))
                    logs['exc_info'] = logs_tmp_var['exc_info'] if 'exc_info' in logs_tmp_var else ''

                    #should update database bash logs
            else:
                status = find_bash_attr(bash_id,'status')
                logs = json.loads(find_bash_attr(bash_id,'logs'))
            
            status = status if status else 'not_found'
            if not logs:
                logs = {'output':'', 'error':'', 'exc_info':''}

# ================Download Log Started===========================
            download_status = 'not_found'
            download_logs = {}
            no_exception, download_job = rq_instance.job_fetch(download_id)
            exc_info_download_info = 'No exc_info or download log has expired.'
            if no_exception:
                download_status = download_job.get_status()
                if download_job.result:
                    download_logs = json.loads(download_job.result)
                else:
                    download_logs = {'output': 'No stdout', 'error': 'No stderr'}

                if download_job.exc_info:
                    download_logs['exc_info'] = download_job.exc_info
                else:
                    download_logs['exc_info'] = exc_info_download_info

                if download_logs['exc_info'] == "null" or not download_logs['exc_info']:
                    download_logs['exc_info'] = exc_info_download_info
            download_status = download_status if download_status else 'not_found' 

            if not download_logs:
                download_logs = {'output':'No stdout', 'error':'No stderr', 'exc_info': exc_info_download_info}

            return jsonify({
                "status": status, 
                "logs": logs,
                "download_status": download_status,
                "download_logs": download_logs
                })


class MIntcastTaskDefaultSetting(MethodView):
    def __init__(self):
        self.mongo_client = pymongo.MongoClient(current_app.config['MONGODB_DATABASE_URI'])
        self.mongo_db = self.mongo_client["mintcast"]
        self.mongo_mintcast_default = self.mongo_db["metadata"]

    def get(self):
        ret = self.mongo_mintcast_default.find_one({'type': 'minty-mintcast-cmd-parameter-setting'}, {"_id": False})
        if ret:
            return jsonify(dict(ret))
        else:
            return jsonify({'status': 404})

    def post(self):
        name = request.form['name']
        status = request.form['status']
        setting = {name:True} if status =='true' else {name:False}
        self.mongo_mintcast_default.update_one(
            {"type":"minty-mintcast-cmd-parameter-setting"},
            {'$set':setting},
            upsert=True

        )
        return jsonify({"status": "ok","name":name,"status":status})

    def __del__(self):
        self.mongo_client.close()

class MIntcastTaskDefaultSettingController(MethodView):
    def __init__(self):
        self.mongo_client = pymongo.MongoClient(current_app.config['MONGODB_DATABASE_URI'])
        self.mongo_db = self.mongo_client["mintcast"]
        self.mongo_mintcast_default_controller = self.mongo_db["metadata"]

    def get(self):
        ret = self.mongo_mintcast_default_controller.find_one({'type': 'minty-dashboard-setting'}, {"_id": False})
        if ret:
            return jsonify(dict(ret))
        else:
            return jsonify({'status': 404})

    def post(self):
        name = request.form['name']
        status = request.form['status']
        setting = {name:True} if status =='true' else {name:False}
        self.mongo_mintcast_default_controller.update_one(
            {"type":"minty-dashboard-setting"},
            {'$set':setting},
            upsert=True

        )
        return jsonify({"status": "ok","name":name,"status":status})

    def __del__(self):
        self.mongo_client.close()
