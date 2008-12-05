import web
render = web.template.render('templates/')

urls = (
	'/', 'index',
	'/post/add', 'add',
	'/post/(\d+)', 'post',
	'/post/(\d+)/edit', 'edit',
	'/post/(\d+)/delete', 'delete',
	'/post/(\d+)/comment', 'comment',
	'/post/(\d+)/comment/(\d+)/delete', 'comment_delete',
)

app = web.application(urls, globals())

db = web.database(dbn='mysql', user='root', pw='', db='woblag_development')

class index:
	def GET(self):
		p = db.query("select id, title, body, (select count(*) from comment where belongs_to = post.id) as comment_count from post;")
		return render.index(p)

class add:
	def GET(self):
		p = db.select('post')
		return render.add(p)
		
	def POST(self):
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
	def GET(self, post_id):
		p = db.select('post', where="id=$post_id", vars=locals())
		c = db.select('comment', where="belongs_to=$post_id", vars=locals())
		return render.post(p,c)
		
class delete:
	def GET(self, post_id):
		n = db.delete('post', 'id = '+post_id)
		raise web.seeother('/')

class comment:
	def POST(self, post_id):
		i = web.input()
		n = db.insert('comment', belongs_to=post_id, author=i.author, body=i.body)
		raise web.seeother('/')

class comment_delete:
	def GET(self, post_id, comment_id):
		n = db.delete('comment', 'id ='+comment_id)
		raise web.seeother('/post/'+post_id)
		
if __name__ == "__main__": app.run()