
import os
MINTCAST_PATH = os.environ.get('MINTCAST_PATH')

from app.models import Bash,db
from app.job import run, excep,add

def combine(args):
	res=" "
	for key in args:
		if(args[key]!='' and args[key]!=None and args[key]!=False and key!="id" and key!="_sa_instance_state" and key!="rqids" and key!="status"):
			param = key.replace("_","-")
			if(args[key]==True):
				res+="--"+param+" "
			else:
				if key=="with_shape_file" or key =="color_map":
					res+="--"+param+" "+"{} {}".format(MINTCAST_PATH,args[key])+" "
				else:
					res+="--"+param+" "+"{}".format(args[key])+" "
	return res

#find one by id 
def findcommand_by_id(id):
	bash = Bash.query.filter_by(id = id).first()
	if bash is None:
		return "no bash"
	if(bash.command!=''):
		return bash.command
	return combine(vars(bash))

def findbash_by_id(id):
	bash = Bash.query.filter_by(id = id).first()
	return bash


#find all
def find_all():
	bashes = Bash.query.order_by("id").all()
	# res=[]
	# for bash in bashes:
	# 	 res.append(combine(vars(bash)))
	return bashes
	
	

# argument is a dic
def addbash(**bash):
	newbash = Bash(**bash)
	db.session.add(newbash)
	db.session.commit()
	#print (bash)

#delete this bash
def deletebash(id):
    bash = Bash.query.filter_by(id = id).first()
    db.session.delete(bash)
    db.session.commit()

#update bash
def updatebash(id,**kwargs):
	bash = Bash.query.filter_by(id = id).first()
	for key in kwargs:
		setattr(bash,key,kwargs[key])
	
	db.session.commit()

def findbashattr(id,attr):
	bash = Bash.query.filter_by(id = id).first()

	return bash._asdict()[attr]


def add_job_id(bashid,jobid):
	bash = Bash.query.filter_by(id = bashid).first()
	setattr(bash,"rqids",jobid)
	db.session.commit()

def runbash(bashid):
	# command = findcommand_by_id(bashid)
	# job = run.queue(command)
	# job = excep.queue()
	job = add.queue(1,2,bashid)
	add_job_id(bashid,job.id)
