import web
render = web.template.render('templates/')

urls = (
	'/', 'index',
	'/add', 'add',
	'/post/(\d+)', 'post',
	'/post/(\d+)/edit', 'edit',
	'/post/(\d+)/delete', 'delete',
)

app = web.application(urls, globals())

db = web.database(dbn='mysql', user='root', pw='', db='woblag_development')

class index:
	def GET(self):
		p = db.select('blog')
		return render.index(p)

class add:
	def GET(self):
		p = db.select('blog')
		return render.add(p)
		
	def POST(self):
		i = web.input()
		n = db.insert('blog', title=i.title, body=i.body)
		raise web.seeother('/')

class edit:
	def GET(self, post_id):
		p = db.query("select * from blog where id = $post_id", vars=locals())
		return render.edit(p)
		
	def POST(self, post_id):
		i = web.input()
		n = db.update('blog', 'id = '+post_id, title=i.title, body=i.body)
		raise web.seeother('/')

class post:
	def GET(self, post_id):
		p = db.query("select * from blog where id = $post_id", vars=locals())
		return render.post(p)
		
class delete:
	def GET(self, post_id):
		n = db.delete('blog', 'id = '+post_id)
		raise web.seeother('/')
		
if __name__ == "__main__": app.run()