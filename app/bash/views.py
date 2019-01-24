from flask import jsonify, request, url_for, redirect, current_app, render_template, flash, make_response
from flask.views import MethodView

from .bash_helper import *
from app.job import *
import requests
import os
import flask_rq2

from app.job import rq_instance

import ast
class DeleteBash(MethodView):
	def get(self, bash_id):
		deletebash(bash_id)
		return redirect(url_for('bash.bash_list'))

class AddBash(MethodView):
	def get(self):
		headers = {'Content-Type': 'text/html'}
		bash = find_all()[0]
		bash = vars(bash)
		txt = []
		boolean = []
		for key in bash:
			if(key != "_sa_instance_state" and key != 'id'):
				if type(bash[key]) == type(True):
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
		addbash(**newbash)
	 
		return redirect(url_for('bash.bash_list'))

class Bash(MethodView):

	def get(self,bash_id = None):
		headers = {'Content-Type': 'text/html'}
		if bash_id is None:
			return "none"
		else:
			bash = find_bash_by_id(bash_id)
			bash = vars(bash)
			txt = []
			boolean = []
			for key in bash:
				if(key != "_sa_instance_state" and key != 'id'):
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
			if result[key]=='on':
				newbash[key]=True
			else:
				newbash[key]=result[key]
		updatebash(bash_id,**newbash)
	   
		return redirect(url_for('bash.bash_list'))
		#return make_response(render_template('bash/bashres.html',res = newbash),200,headers)

class BashList(MethodView):
	def get(self):
		bashes = find_all()
		res = []
		ids = []
		for bash in bashes:
			bash=vars(bash)
			bash['command'] = find_command_by_id(bash['id'])
			res.append(bash)
			ids.append(str(bash['id']))
		th = []
		# for key in vars(bashes[0]):
		#     if(key != "_sa_instance_state"):
		#         th.append(key)
		th.append("command")
		th.sort()
		headers = {'Content-Type': 'text/html'}
		return make_response(render_template('bash/bashList.html',th = th,res = res,ids = ids),200,headers)

	def post(self):
		para = request.form
		bash_ids = para['bash_ids']
		setting={"dev_mode_off":False,"disable_new_res":False,"scp_to_default_server":False}
		for key in para:
			if para[key] =='on':
				setting[key] = True
		bash_ids = ast.literal_eval(bash_ids)
		for bash_id in bash_ids:
			updatebash(bash_id,**setting)
		return jsonify({"status": "success"})


class Run(MethodView):
	def post(self):
		bashid = request.form["bashid"]
		bash = findbash_by_id(bashid)
		bash = vars(bash)
		if (bash[data_file_path]=='' and os.path.exists(bash[dir])) or (os.path.isfile(bash[data_file_path])):
			runbash(bashid)
		else:
			r = requests.get(url_for('minty.visualize_action',bash_id=bash['md5vector']))
		return jsonify({"status": "queued"})

class Status(MethodView):
	def post(self):
		if 'type' in request.form and request.form['type'] == 'batch':
			bash_ids = list(map(int, filter(lambda x: x  !=  '',request.form['bashid'].split(',') ) ))
			job_ids = request.form['jobid'].split(',')
			status = []
			results = []
			for idx, job_id in enumerate(job_ids):
				no_exception, job = rq_instance.job_fetch(job_id)
				if no_exception:
					status.append(job.get_status())
					results.append(job.result)
					updatebash(bash_ids[idx],status = job.get_status())
				else:
					status.append('')
					results.append(find_bash_attr(bash_ids[idx],'status'))
				   
			return jsonify({ "job_status": status, "job_result": results })
		else:
			bashid = request.form['bashid']
			job_id = request.form['jobid']
			# print(jobid)
			status = ''
			result = ''
			exc_info = ''

			no_exception, job = rq_instance.job_fetch(job_id)
			if no_exception:
				status = job.get_status()
				result = job.result
				exc_info = job.exc_info
			else:
				status = '' 
				result = ''
				exc_info = job

			return jsonify({
				"job_status": status, 
				"result": result, 
				"exc_info": exc_info if exc_info else 'No Log'
				})
