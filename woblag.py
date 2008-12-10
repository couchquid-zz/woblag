# -*- coding: utf8 -*-
import web
from web import form
from hashlib import sha1
import time
import re
import unicodedata

render = web.template.render('templates/')

urls = (
	'/', 'index',
	'/page/:([0-9])*', 'index',
	'/archive/(\d+)/(\d+)', 'archive',
	'/admin/login', 'login',
	'/admin/logout', 'logout',
	'/post/add', 'add',
	'/post/(\d+):([\a-z_]+)', 'post',
	'/post/edit/:(\d+)', 'edit',
	'/post/delete/:(\d+)', 'delete',
	'/post/comment/:(\d+)', 'comment',
	'/post/delete/comment/:(\d+)', 'comment',
)

#config
app = web.application(urls, locals())
db = web.database(dbn='mysql', user='root', pw='', db='woblag_development')

#work around for creating a session
if web.config.get('_session') is None:
	session = web.session.Session(app, web.session.DiskStore('sessions'), initializer={'user': 'anonymous'})
	web.config._session = session
else:
	session = web.config._session

username = "admin"
password = "3da541559918a808c2402bba5012f6c60b27661c"

def slugify(value):
	#remove_list = ["a", "an", "as", "at", "by", "for", "is", "in", "of", "off", "on", "than", "the", "to"];
	value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
	#for a in remove_list:
	#	value = unicode(re.sub(r'\b'+a+r'\b', '', value))
		
	value = unicode(re.sub('\s+', '-', value))
	return value.strip().lower()

class index:
	def GET(self, page=0):
		#pagination
		page = 0 if not page else int(page)
		num_of_posts = db.query("SELECT COUNT(*) AS count FROM post")[0].count
		offset = page * 5
		
		next_page = page + 1 if (page + 1) * 5 < num_of_posts else None
		previous_page = page - 1 if page > 0 else None
		
		posts = db.select('post', order='created DESC', limit=5, offset=offset, vars=locals())
		posts_full = db.select('post', vars=locals())
		comments = db.query('SELECT id, (SELECT COUNT(*) FROM comment WHERE belongs_to = post.id) AS comment_count FROM post;')
		
		#archives
		monthyear = {}

		for post in posts_full:
			if post.created.strftime('%B %Y') not in monthyear:
				monthyear[post.created.strftime('%B %Y')] = post.created.strftime('%Y/%m')
		
		return render.index(posts, comments, session.user, next_page, previous_page, monthyear)

class add:
	
	addpost_form = form.Form(
		form.Textbox("title", form.notnull, description="Title:"),
		form.Textarea("body", form.notnull, description="Text:"),
		form.Button("submit", type="submit", description="Add post"),
	)
	
	def GET(self):
		posts = db.select('post', vars=locals())
		form = self.addpost_form
		return render.add(posts, form)
		
	def POST(self):
		form = self.addpost_form
		if not form.validates():
			posts = db.select('post', vars=locals())
			return render.add(posts, form)
		else:
			i = web.input()
			db.insert('post', title=i.title, body=i.body, slug=slugify(i.title))
			raise web.seeother('/')

class edit:
	
	editpost_form = form.Form(
		form.Textbox("title", form.notnull, value='', description="Title:"),
		form.Textarea("body", form.notnull, value='', description="Text:"),
		form.Button("submit", type="submit", description="Edit"),
	)
	
	def GET(self, post_id):
		posts = db.select('post', where='id=$post_id', vars=locals())
		form = self.editpost_form
		return render.edit(posts, form)
		
	def POST(self, post_id):
		posts = db.select('post', where='id=$post_id', vars=locals())
		form = self.editpost_form
		if not form.validates():
			return render.edit(posts, forms)
		else:
			i = web.input()
			db.update('post', 'id = '+post_id, title=i.title, body=i.body, vars=locals())
			raise web.seeother('/')

class post:
	
	addcomment_form = form.Form(
		form.Textbox("author", form.notnull, description="Name:"),
		form.Textarea("body", form.notnull, description="Text:"),
	)
	
	def GET(self, post_id, post_title):
		form = self.addcomment_form
		posts = db.select('post', where='id=$post_id', vars=locals())
		comments = db.select('comment', where='belongs_to=$post_id', order='created ASC',vars=locals())
		return render.post(posts, comments, form, session.user)
		
class archive:
	def GET(self, year, month):
		posts = db.select('post', where='created like $year and created like $month', order='created DESC', vars={'year':'%'+year+'%', 'month':'%'+month+'%'})					
		return render.archive(posts, session.user)
		
class delete:
	def GET(self, post_id):
		if session.user == 'admin':
			db.delete('post', where='id = '+post_id)
			db.delete('comment', where='belongs_to = '+post_id)
			raise web.seeother('/')
		else:
			return "You don't have access to this."

class comment:
	def GET(self, comment_id):
		if session.user == 'admin':
			db.delete('comment', 'id = '+comment_id)
			raise web.seeother('/')
		else:
			return "You don't have access to this."
			
	def POST(self, post_id):
		form = post.addcomment_form()
		if not form.validates():
			posts = db.select('post', where='id=$post_id', vars=locals())
			comments = db.select('comment', where='belongs_to=$post_id', order='created ASC', vars=locals())
			return render.post(posts, comments, form)
		else:
			i = web.input()
			db.insert('comment', belongs_to=post_id, author=i.author, body=i.body)
			raise web.seeother('/')
			
class login:
	
	login_form = form.Form(
		form.Textbox("username", form.Validator("Unknown username.", lambda x: x in username), description="Username:"),
		form.Password("password", description="Password:"),
		validators = [form.Validator("Username and password did not match.",
					lambda i: i.username in username and sha1(i.password).hexdigest() in password)]
	)
	
	def GET(self):
		form = self.login_form()
		return render.login(session.user, form)
	
	def POST(self):
		form = self.login_form()
		if not form.validates():
			return render.login(session.user, form)
		else:
			session.user = form['username'].value
			return render.login(session.user, form)

class logout:
	def GET(self):
		session.kill()
		raise web.seeother('/')
		
if __name__ == "__main__":
	app.run()