from flask import Flask,render_template,request,redirect,make_response
import sqlite3
import hashlib
from datetime import datetime
from MobBook import app
from MobBook import Secret


DataBaseFilePath ='Anthology.db';

def RepresentsInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

def GetNode(NodeId):
	global DataBaseFilePath
	conn = sqlite3.connect(DataBaseFilePath)
	c = conn.cursor()		
	c.execute('''CREATE TABLE IF NOT EXISTS ActI (Id INTEGER PRIMARY KEY AUTOINCREMENT,Parent int,Rating int,Body text,Hits int)''')
	c.execute('SELECT * FROM ActI WHERE Id=?', (NodeId,))
	LstNode =c.fetchone()
	c.close();	
	return {'Id':LstNode[0],'Parent':LstNode[1],'Rating':LstNode[2],'Body':LstNode[3],'Hits':LstNode[4]}
	


def GetNodeChildren(NodeId):			
	global DataBaseFilePath
	conn = sqlite3.connect(DataBaseFilePath)
	c = conn.cursor()	
	c.execute('''CREATE TABLE IF NOT EXISTS ActI (Id INTEGER PRIMARY KEY AUTOINCREMENT,Parent int,Rating int,Body text,Hits int)''')
	c.execute('SELECT * FROM ActI WHERE Parent=? ORDER BY Rating DESC', (NodeId,))
	LstChild_list = c.fetchall()
	c.close();	
	Child_list =[]
	for C in LstChild_list:
		Child_list.append({'Id':C[0],'Parent':C[1],'Rating':C[2],'Body':C[3],'Hits':C[4]})
	return Child_list


def InsertNodeIntoDB(Node):
	if (Node['Body'] !=""):
		global DataBaseFilePath
		conn = sqlite3.connect(DataBaseFilePath)
		c = conn.cursor()
		c.execute("INSERT INTO ActI(Parent,Rating,Body,Hits) VALUES (?,0,?,1)",(Node['Parent'],Node['Body'],))			
		NextNodeId=c.lastrowid
		c.close()
		conn.commit()
		return {'Id': NextNodeId,'Parent':Node['Parent'],'Rating':0, 'Body':Node['Body'], 'Hits':1}
	else:
		return None

def IDSafeNode(NodeId=None):
	if (NodeId==None or not RepresentsInt(NodeId)):
		return None
	else:
		Node=GetNode(NodeId)		
		if (Node==None):
			return None
		return Node
def CreateHash(IP = None):
	if (IP != None):
		Hash =hashlib.md5()
		Hash.update(IP.encode('utf-8'))
		Hash.update(datetime.now().replace(second=0, microsecond=0).ctime().encode('utf-8'))
		Hash.update(Secret.SecretText.encode('utf-8'))
		return Hash.digest()
	return None
def UpRateNode(NodeId= None):
	if (IDSafeNode(NodeId)!=None):
		global DataBaseFilePath
		conn = sqlite3.connect(DataBaseFilePath)
		c = conn.cursor()
		c.execute("UPDATE ActI SET Rating=Rating+5 WHERE Id=?;",(NodeId,))	
		c.close()
		conn.commit()
def DownRateNode(NodeId= None):
	if (IDSafeNode(NodeId)!=None):
		global DataBaseFilePath
		conn = sqlite3.connect(DataBaseFilePath)
		c = conn.cursor()
		c.execute("UPDATE ActI SET Rating=Rating-1 WHERE Id=?;",(NodeId,))	
		c.close()
		conn.commit()	
def AddHit(NodeId= None):
	if (IDSafeNode(NodeId)!=None):
		global DataBaseFilePath
		conn = sqlite3.connect(DataBaseFilePath)
		c = conn.cursor()
		c.execute("UPDATE ActI SET Hits=Hits+1 WHERE Id=?;",(NodeId,))	
		c.close()
		conn.commit()	
		
@app.route('/About')
def About():	
	return render_template('About.html')

@app.route('/Faq')
def Faq():	
	return "Faq Page"

@app.route('/<test>')
def Test(test= None):	
	return redirect('/')

@app.route('/StorySoFar/<NodeId>')
def CompileStory(NodeId):
	Node= IDSafeNode(NodeId)
	if (Node==None):
		return redirect('/')
	book = [Node,]
	while (Node['Parent'] !=0):
		Node=GetNode(Node['Parent'])	
		book.append(Node)
	book.reverse()
	return render_template('StorySoFar.html', book=book)

def CompileResponce(_request=None,NodeId=None):
	Node=IDSafeNode(NodeId)
	if (Node !=None and _request !=None):
		if (request.cookies.get('Btn'+str(NodeId))=="True"):
			Rated=True
		else:
			Rated=False
		AddHit(NodeId)
		Child_list=GetNodeChildren(NodeId)
		if (_request.method=='POST'):			
			if ('TxtAddNode' in request.form):
				NextNode= InsertNodeIntoDB({'Parent':NodeId,'Body':request.form['TxtAddNode']})
				if NextNode != None:
					return make_response(redirect('/ID/'+str(NextNode['Id'])))
			if (_request.cookies.get('TimeOut')==str(CreateHash(_request.remote_addr))):	
				if ('voteUp' in _request.form):
					UpRateNode(NodeId)
					Resp=make_response(redirect('/ID/'+str(Node['Id'])))
					Resp.set_cookie('Btn'+str(NodeId), "True")
					return Resp
				if ('voteDown' in _request.form):
					DownRateNode(NodeId)
					Resp=make_response(redirect('/ID/'+str(Node['Id'])))
					Resp.set_cookie('Btn'+str(NodeId), "True")
					return Resp
		return make_response(render_template('Basic_Layout.html',	Child_list=Child_list, Node= Node, Rated=Rated))
	return None

@app.route('/ID/<NodeId>',methods=['GET','POST'])
def NodePage(NodeId=None):
	Resp=CompileResponce(request,NodeId)
	if Resp==None:
		return redirect('/')		
	if (request.method=="GET"):
		Resp.set_cookie('TimeOut', CreateHash(request.remote_addr))
	return Resp

@app.route('/',methods=['GET','POST'])
def home():	
		NodeId=1
		Resp=CompileResponce(request,NodeId)
		if Resp==None:
			return "error"
		if (request.method=="GET"):
			Resp.set_cookie('TimeOut', str(CreateHash(request.remote_addr)))
		print (request)
		return Resp