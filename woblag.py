import web
from web import form
from hashlib import sha1

render = web.template.render('templates/')

urls = (
	'/', 'index',
	'/login', 'login',
	'/post/add', 'add',
	'/post/(\d+)', 'post',
	'/post/(\d+)/edit', 'edit',
	'/post/(\d+)/delete', 'delete',
	'/post/(\d+)/comment', 'comment',
	'/post/(\d+)/comment/(\d+)/delete', 'comment_delete',
)

#Config
app = web.application(urls, globals())
db = web.database(dbn='mysql', user='root', pw='', db='woblag_development')

username = "admin"
password = "3da541559918a808c2402bba5012f6c60b27661c"


class index:
	def GET(self):
		p = db.query("select id, title, body, created, (select count(*) from comment where belongs_to = post.id) as comment_count from post;")
		return render.index(p)

class add:
	
	addpost_form = form.Form(
		form.Textbox("title",
			form.notnull,
		),
		form.Textarea("body",
			form.notnull,
		),
	)
	
	def GET(self):
		p = db.select('post')
		form = addpost_form
		return render.add(p, form)
		
	def POST(self):
		form = addpost_form
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
		),
		form.Textarea("body",
			form.notnull,
		),
	)
	
	def GET(self, post_id):
		form = self.addcomment_form
		p = db.select('post', where="id=$post_id", vars=locals())
		c = db.select('comment', where="belongs_to=$post_id", vars=locals())
		return render.post(p,c,form)
		
class delete:
	def GET(self, post_id):
		n = db.delete('post', 'id = '+post_id)
		raise web.seeother('/')

class comment:
	def POST(self, post_id):
		form = addcomment_form()
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
		n = db.delete('comment', 'id ='+comment_id)
		raise web.seeother('/post/'+post_id)
		
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
		return render.login(form)
	
	def POST(self):
		form = self.login_form()
		if not form.validates():
			return render.login(form)
		else:
			raise web.seeother('/')
		
if __name__ == "__main__": app.run()