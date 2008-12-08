import web
from web import form
from hashlib import sha1

render = web.template.render('templates/')

urls = (
	'/', 'index',
	'/page/([0-9])*', 'index',
	'/archive/(\d+)/(\d+)', 'archive',
	'/login', 'login',
	'/logout', 'logout',
	'/post/add', 'add',
	'/post/(\d+)', 'post',
	'/post/(\d+)/edit', 'edit',
	'/post/(\d+)/delete', 'delete',
	'/post/(\d+)/comment', 'comment',
	'/post/(\d+)/comment/(\d+)/delete', 'comment_delete',
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

class index:
	def GET(self, page=0):
		#pagination
		page = 0 if not page else int(page)
		num_of_posts = db.query("SELECT COUNT(*) AS count FROM post")[0].count
		offset = page * 5
		
		next_page = page + 1 if (page + 1) * 5 < num_of_posts else None
		previous_page = page - 1 if page > 0 else None
		
		p = db.select("post", order="created DESC", limit=5, offset=offset)
		comments = db.query("SELECT id, (SELECT COUNT(*) FROM comment WHERE belongs_to = post.id) AS comment_count FROM post;")
		return render.index(p, comments, session.user, next_page, previous_page)

class add:
	
	addpost_form = form.Form(
		form.Textbox("title",
			form.notnull,
			description="Title:",
		),
		form.Textarea("body",
			form.notnull,
			description="Text:",
		),
	)
	
	def GET(self):
		p = db.select('post')
		form = self.addpost_form
		return render.add(p, form)
		
	def POST(self):
		form = self.addpost_form
		if not form.validates():
			p = db.select('post')
			return render.add(p, form)
		else:
			i = web.input()
			n = db.insert('post', title=i.title, body=i.body)
			raise web.seeother('/')

class edit:
	def GET(self, post_id):
		p = db.select('post', where="id=$post_id", vars=locals())
		return render.edit(p)
		
	def POST(self, post_id):
		i = web.input()
		n = db.update('post', 'id = '+post_id, title=i.title, body=i.body)
		raise web.seeother('/')

class post:
	
	addcomment_form = form.Form(
		form.Textbox("author",
			form.notnull,
			description="Name:",
		),
		form.Textarea("body",
			form.notnull,
			description="Text:",
		),
	)
	
	def GET(self, post_id):
		form = self.addcomment_form
		p = db.select('post', where="id=$post_id", vars=locals())
		c = db.select('comment', where="belongs_to=$post_id", order="created DESC",vars=locals())
		return render.post(p,c,form,session.user)
		
class archive:
	def GET(self, year, month):
		p = db.select('post', where="created like $year and created like $month", order="created DESC", vars={'year':'%'+year+'%', 'month':'%'+month+'%'})
		return render.archive(p, session.user)
		
class delete:
	def GET(self, post_id):
		if session.user == 'admin':
			n = db.delete('post', 'id = '+post_id)
			raise web.seeother('/')
		else:
			return "You don't have access to this."

class comment:
	def POST(self, post_id):
		form = post.addcomment_form()
		if not form.validates():
			p = db.select('post', where="id=$post_id", vars=locals())
			c = db.select('comment', where="belongs_to=$post_id", vars=locals())
			return render.post(p,c,form)
		else:
			i = web.input()
			n = db.insert('comment', belongs_to=post_id, author=i.author, body=i.body)
			raise web.seeother('/')

class comment_delete:
	def GET(self, post_id, comment_id):
		if session.user == 'admin':
			n = db.delete('comment', 'id ='+comment_id)
			raise web.seeother('/post/'+post_id)
		else:
			return "You don't have access to this."
		
class login:
	
	login_form = form.Form(
		form.Textbox("username",
			form.Validator("Unknown username.", lambda x: x in username),
			description="Username:"),
		form.Password("password",
			description="Password:"),
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