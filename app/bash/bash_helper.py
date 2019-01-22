import sys
sys.path.append("..")
from app.models import Bash,db

def combine(args):
	res=" "
	for key in args:
		if(args[key]!='' and args[key]!=False and key!="id" and key!="_sa_instance_state"):
			param=key.replace("_","-")
			if(args[key]==True):
				res+="--"+param+" "
			else:
				res+="--"+param+" "+"{}".format(args[key])+" "
			
	return res

#find one by id 
def findcommand_by_id(id):
	bash=Bash.query.filter_by(id=id).first()
	if bash is None:
		return "no bash"
	if(bash.command!=''):
		return bash.command
	return combine(vars(bash))

def findbash_by_id(id):
	bash=Bash.query.filter_by(id=id).first()
	return bash


#find all
def find_all():
	bashes=Bash.query.all()
	# res=[]
	# for bash in bashes:
	# 	 res.append(combine(vars(bash)))
	return bashes
	
	

# argument is a dic
def addbash(**bash):
	newbash=Bash(**bash)
	db.session.add(newbash)
	db.session.commit()
	#print (bash)

#delete this bash
def deletebash(id):
    bash = Bash.query.filter_by(id=id).first()
    db.session.delete(bash)
    db.session.commit()

#update bash
def updatebash(id,**kwargs):
	bash=Bash.query.filter_by(id=id).first()
	for key in kwargs:
		setattr(bash,key,kwargs[key])
	
	db.session.commit()
