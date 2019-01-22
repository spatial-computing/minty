from flask import jsonify, request, url_for, redirect, current_app, render_template, flash, make_response
from flask.views import MethodView
from flask_restful import Resource

from .bash_helper import *
from app.job import *

import time

class DeleteBash(MethodView):

	def get(self,bash_id):
		deletebash(bash_id)
		return redirect(url_for('bash.bash_list'))

class AddBash(MethodView):
	
	def get(self):
		headers = {'Content-Type': 'text/html'}
		bash=find_all()[0]
		bash=vars(bash)
		txt=[]
		boolean=[]
		for key in bash:
			if(key!="_sa_instance_state" and key!='id'):
				if type(bash[key]) == type(True):
					boolean.append(key)
				else:
					txt.append(key)
		txt.sort()
		boolean.sort()
		return make_response(render_template('bash/bash.html',txt=txt,boolean=boolean,bash={}),200,headers)
 
	def post(self):
		headers = {'Content-Type': 'text/html'}
		result = request.form
		newbash={}
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

	def get(self,bash_id=None):
		headers = {'Content-Type': 'text/html'}
		if bash_id is None:
			return "none"
		else:
			bash=findbash_by_id(bash_id)
			bash=vars(bash)
			txt=[]
			boolean=[]
			for key in bash:
				if(key!="_sa_instance_state" and key!='id'):
					if type(bash[key]) == type(True):
						boolean.append(key)
					else:
						txt.append(key)
			txt.sort()
			boolean.sort()
			return make_response(render_template('bash/bash.html',txt=txt,boolean=boolean,bash=bash),200,headers)

	

# infact it is a put method to update the bash
	def post(self,bash_id):
		headers = {'Content-Type': 'text/html'}
		result = request.form
		newbash={}
		for key in result:
			if result[key]=='on':
				newbash[key]=True
			else:
				newbash[key]=result[key]
		updatebash(bash_id,**newbash)
	   
		return redirect(url_for('bash.bash_list'))
		#return make_response(render_template('bash/bashres.html',res=newbash),200,headers)

class BashList(MethodView):
	def get(self):
		bashes=find_all()
		res=[]
		for bash in bashes:
			res.append(vars(bash))
		th=[]
		# for key in vars(bashes[0]):
		#     if(key!="_sa_instance_state"):
		#         th.append(key)
		th.append("command")
		th.sort()
		headers = {'Content-Type': 'text/html'}
		return make_response(render_template('bash/bashList.html',th=th,res=res),200,headers)

class Run(MethodView):
	def post(self):
		bashid=request.form["bashid"]
		command=findcommand_by_id(bashid)
		job = run.queue(command)
		print(job.id)
		add_job_id(bashid,jobid)
		# job=add.queue(1,2,bashid)

		return jsonify({"status": "queued"})

