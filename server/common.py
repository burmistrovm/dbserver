import json, MySQLdb
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

MYSQL_DUPLICATE_ENTITY_ERROR = 1062

class MyDB:
	def __init__(self):
		self.connection = None
		self.cursor = None
		self.initConnAndCursor()

	def execute(self, sql, args=(), post=False):
		self.cursor.execute(sql, args)
		if post:
			self.connection.commit()
			return self.cursor.lastrowid

		return self.cursor.fetchall()

	def initConnAndCursor(self):
		if not self.connection or not self.connection.open:
			self.connection = MySQLdb.connect(host="localhost", user="django", passwd="24081994", db="dbproj")
			self.cursor = self.connection.cursor()
			self.connection.set_character_set('utf8')

	def closeConnection(self):
		self.connection.close()
db = MyDB()

@csrf_exempt
def clear(request):
	db.execute("""DELETE Forum.* FROM Forum;""", post=True)
	db.execute("""DELETE User.* FROM User;""", post=True)
	db.execute("""DELETE Post.* FROM  Post;""")
	db.execute("""DELETE Thread.* FROM  Thread;""", post=True)
	db.execute("""DELETE Subscription.* FROM Subscription;""", post=True)
	db.execute("""DELETE Follower.* FROM Follower;""", post=True)
	return JsonResponse({"code": 0, "response": "OK"})

def str_to_json(value, is_bool=False):
	if is_bool:
		return value != 0
	if value == "NULL":
		return None
	return value

def get_user_dict(email):
	user_list_sql = db.execute("""SELECT user, email, name, username, isAnonymous, about FROM User \
		WHERE email = %(email)s;""", {'email': email})
	if not user_list_sql:
		return dict()

	user_sql = user_list_sql[0]

	return {'id': str_to_json(user_sql[0]),
			'email': str_to_json(user_sql[1]),
			'name': str_to_json(user_sql[2]),
			'username': str_to_json(user_sql[3]),
			'isAnonymous': str_to_json(user_sql[4], True),
			'about': str_to_json(user_sql[5]),
			'subscriptions': get_subscribed_threads_list(user_sql[1])}

def get_forum_dict(short_name):
	forum_list_sql = db.execute("""SELECT forum, name, short_name, user FROM Forum \
		WHERE short_name = %(short_name)s;""", {'short_name': short_name})
	if not forum_list_sql:
		return dict()
	forum_sql = forum_list_sql[0]
	return {'id': str_to_json(forum_sql[0]),
			'name': str_to_json(forum_sql[1]),
			'short_name': str_to_json(forum_sql[2]),
			'user': str_to_json(forum_sql[3])}

def get_post_list(user="", thread="", forum="", since="", order="", limit="",sort="flat"):
	if thread != "" and thread != None:
		where = "thread = '{}' ".format(thread)

	if user != "":
		where = "user = '{}'".format(user)

	elif forum != "" and forum != None:
		where = "forum = '{}' ".format(forum)

	since_sql = ""
	if since != None:
		since_sql = """AND date >= '{}'""".format(since)
	order_sql = """ORDER BY date """
	if order != None:
		order_sql = order_sql + """{}""".format(order)
	limit_sql = ""
	if limit != None:
		limit_sql = """LIMIT {}""".format(limit)


	if sort == "flat":
		sql = "SELECT post, user, thread, forum, message, parent, date, likes, dislikes, points, \
			isSpam, isEdited, isDeleted, isHighlighted, isApproved, mpath FROM Post \
			WHERE {where} {since} {order} {limit};".format(where = where, order = order_sql, since = since_sql, limit = limit_sql)
		post_list_sql = db.execute(sql)


	if sort == "tree":
		sql = "SELECT post, user, thread, forum, message, parent, date, likes, dislikes, points, \
			isSpam, isEdited, isDeleted, isHighlighted, isApproved, mpath FROM Post \
			WHERE {where} and parent IS NULL {since} {order} {limit};".format(where = where, order = order_sql, since = since_sql, limit = limit_sql)
		post_parent_list_sql = db.execute(sql)
		lenght = len(post_parent_list_sql)
		post_list_sql = list()
		for post in post_parent_list_sql:
			parent_mpath = post[15]
			post_child_list_sql = db.execute(("SELECT post, user, thread, forum, message, parent, date, likes, dislikes, points, \
			isSpam, isEdited, isDeleted, isHighlighted, isApproved, mpath FROM Post \
			WHERE {where} AND parent IS NOT NULL AND mpath LIKE '{parent}' ORDER BY mpath, date;").format(where = where,parent = parent_mpath +"%%"))
			post_list_sql.append(post)
			post_list_sql.extend(post_child_list_sql)

	if sort == "parent_tree":
		sql = "SELECT post, user, thread, forum, message, parent, date, likes, dislikes, points, \
			isSpam, isEdited, isDeleted, isHighlighted, isApproved, mpath FROM Post \
			WHERE {where} AND parent IS NULL {since} {order} {limit};".format(where = where, order = order_sql, since = since_sql, limit = limit_sql)
		post_parent_list_sql = db.execute(sql)
		lenght = len(post_parent_list_sql)
		post_list_sql = list()
		for post in post_parent_list_sql:
			parent_mpath = post[15]
			post_child_list_sql = db.execute(("SELECT post, user, thread, forum, message, parent, date, likes, dislikes, points, \
			isSpam, isEdited, isDeleted, isHighlighted, isApproved, mpath FROM Post \
			WHERE {where} AND parent IS NOT NULL AND mpath LIKE '{parent}' ORDER BY mpath, date;").format(where = where, parent = parent_mpath +"%%"))
			post_list_sql.append(post)
			post_list_sql.extend(post_child_list_sql)
		limit = len(post_list_sql)
	post_list = list()
	if limit == None:
		limit = len(post_list_sql)
	print(limit)
	i=0
	while (i < int(limit)) and (i < len(post_list_sql)):
		print(i)
		post_list.append({
			'id': str_to_json(post_list_sql[i][0]),
			'user': str_to_json(post_list_sql[i][1]),
			'thread': str_to_json(post_list_sql[i][2]),
			'forum': str_to_json(post_list_sql[i][3]),
			'message': str_to_json(post_list_sql[i][4]),
			'parent': str_to_json(post_list_sql[i][5]),
			'date': post_list_sql[i][6].strftime('%Y-%m-%d %H:%M:%S'),
			'likes': str_to_json(post_list_sql[i][7]),
			'dislikes': str_to_json(post_list_sql[i][8]),
			'points': str_to_json(post_list_sql[i][9]),
			'isSpam': str_to_json(post_list_sql[i][10], True),
			'isEdited': str_to_json(post_list_sql[i][11], True),
			'isDeleted': str_to_json(post_list_sql[i][12], True),
			'isHighlighted': str_to_json(post_list_sql[i][13], True),
			'isApproved': str_to_json(post_list_sql[i][14], True),
			'mpath': str_to_json(post_list_sql[i][15])
		})
		i = i+1
	return post_list

def get_thread_list(user="",since="",forum="",limit="",order="ASC"):
	if user != "" and user != None:
		where = "user = '{}'".format(user)
		print('user')
	elif forum != "" and forum != None:
		where = "forum = '{}' ".format(forum)
		print(forum)
	since_sql = ""
	if since != None:
		since_sql = """AND date >= '{}'""".format(since)
	order_sql = """ORDER BY date """
	if order != None:
		order_sql = order_sql + """{}""".format(order)
	limit_sql = ""
	if limit != None:
		limit_sql = """LIMIT {}""".format(limit)
	thread_list_sql = db.execute("""SELECT title, user, forum, message, date, slug, isDeleted, isClosed, thread, posts, points, likes, dislikes FROM Thread \
		WHERE {where} {since} {order} {limit};""".format(where = where, order = order_sql, limit = limit_sql, since = since_sql))
	thread_list = list();
	for thread_sql in thread_list_sql:
		thread_list.append({'title': str_to_json(thread_sql[0]),
			'user': str_to_json(thread_sql[1]), 
			'forum': str_to_json(thread_sql[2]), 
			'message': str_to_json(thread_sql[3]), 
			'date': str_to_json(thread_sql[4]).strftime('%Y-%m-%d %H:%M:%S'),
			'slug': str_to_json(thread_sql[5]), 
			'isDeleted': str_to_json(thread_sql[6]), 
			'isClosed': str_to_json(thread_sql[7]),
			'id':str_to_json(thread_sql[8]),
			'posts':str_to_json(thread_sql[9]),
			'points':str_to_json(thread_sql[10]),
			'likes':str_to_json(thread_sql[11]),
			'dislikes': str_to_json(thread_sql[12]),
			'subscriptions' : get_subscribed_user_list(thread_sql[8])
			})
	return thread_list;

def get_user_list(forum,limit="",order="ASC"):
	order_sql = """ORDER BY name """
	if order != None:
		order_sql = order_sql + """{}""".format(order)
	limit_sql = ""
	if limit != None:
		limit_sql = """LIMIT {}""".format(limit)
	user_list_sql = db.execute("""SELECT DISTINCT u.user, email, name, username, isAnonymous, about FROM User AS u \
		INNER JOIN Post AS p ON(p.user = u.email)\
		WHERE forum = '{forum}' {order} {limit};""".format(forum = forum, order = order_sql, limit = limit_sql))
	print(len(user_list_sql))
	user_list = list();
	for user_sql in user_list_sql:
		user_list.append({'id': str_to_json(user_sql[0]),
			'email': str_to_json(user_sql[1]),
			'name': str_to_json(user_sql[2]),
			'username': str_to_json(user_sql[3]),
			'isAnonymous': str_to_json(user_sql[4], True),
			'about': str_to_json(user_sql[5]),
			'subscriptions': get_subscribed_threads_list(user_sql[1])})
	return user_list;
	

def get_thread_dict(thread):
	thread_list_sql = db.execute("""SELECT title, user, forum, message, date, slug, isDeleted, isClosed, thread, posts, points, likes, dislikes FROM Thread \
		WHERE thread = %(thread)s LIMIT 1;""", {'thread': thread})
	if not thread_list_sql:
		return list()
	thread_sql = thread_list_sql[0]
	return {'title': str_to_json(thread_sql[0]),
			'user': str_to_json(thread_sql[1]), 
			'forum': str_to_json(thread_sql[2]), 
			'message': str_to_json(thread_sql[3]), 
			'date': str_to_json(thread_sql[4]).strftime('%Y-%m-%d %H:%M:%S'),
			'slug': str_to_json(thread_sql[5]), 
			'isDeleted': str_to_json(thread_sql[6]), 
			'isClosed': str_to_json(thread_sql[7]),
			'id':str_to_json(thread_sql[8]),
			'posts':str_to_json(thread_sql[9]),
			'points':str_to_json(thread_sql[10]),
			'likes':str_to_json(thread_sql[11]),
			'dislikes': str_to_json(thread_sql[12]),
			'subscriptions':get_subscribed_user_list(thread_sql[8])
			}

def get_thread_by_id(thread):
	thread_list_sql = db.execute("""SELECT title, user, forum, message, date, slug, isDeleted, isClosed, thread, posts, points, likes, dislikes FROM Thread \
		WHERE thread = %(thread)s LIMIT 1;""", {'thread': thread})
	if not thread_list_sql:
		return list()
	thread_sql = thread_list_sql[0]
	print(thread_sql[8])
	return {'title': str_to_json(thread_sql[0]),
			'user': str_to_json(thread_sql[1]), 
			'forum': str_to_json(thread_sql[2]), 
			'message': str_to_json(thread_sql[3]), 
			'date': str_to_json(thread_sql[4]).strftime('%Y-%m-%d %H:%M:%S'),
			'slug': str_to_json(thread_sql[5]), 
			'isDeleted': str_to_json(thread_sql[6]), 
			'isClosed': str_to_json(thread_sql[7]),
			'id':str_to_json(thread_sql[8]),
			'posts':str_to_json(thread_sql[9]),
			'points':str_to_json(thread_sql[10]),
			'likes':str_to_json(thread_sql[11]),
			'dislikes': str_to_json(thread_sql[12]),
			'subscriptions': get_subscribed_user_list(thread_sql[8])
			}


def get_post_by_id(postId):
	sql = """SELECT post, user, thread, forum, message, parent, date, likes, dislikes, points, \
		isSpam, isEdited, isDeleted, isHighlighted, isApproved, mpath FROM Post \
		WHERE post = %(id)s LIMIT 1;"""

	post_list_sql = db.execute(sql, {'id': postId})
	if not post_list_sql:
		return list()

	post_sql = post_list_sql[0]
	return {'id': str_to_json(post_sql[0]),
			'user': str_to_json(post_sql[1]),
			'thread': str_to_json(post_sql[2]),
			'forum': str_to_json(post_sql[3]),
			'message': str_to_json(post_sql[4]),
			'parent': str_to_json(post_sql[5]),
			'date': post_sql[6].strftime('%Y-%m-%d %H:%M:%S'),
			'likes': str_to_json(post_sql[7]),
			'dislikes': str_to_json(post_sql[8]),
			'points': str_to_json(post_sql[9]),
			'isSpam': str_to_json(post_sql[10], True),
			'isEdited': str_to_json(post_sql[11], True),
			'isDeleted': str_to_json(post_sql[12], True),
			'isHighlighted': str_to_json(post_sql[13], True),
			'isApproved': str_to_json(post_sql[14], True),
			'mpath': str_to_json(post_sql[15])}

def add_post_to_thread(thread):
	db.execute("""UPDATE Thread SET posts = posts + 1 WHERE thread = %(thread)s;""", {'thread': thread}, post=True)

def get_followers_list(email):
	follower_list = db.execute("""SELECT follower FROM Follower
		WHERE followee = %(email)s;""", {'email': email})
	if not follower_list:
		return list()
	return follower_list[0]

def get_following_list(email):
	following_list = db.execute("""SELECT followee FROM Follower
		WHERE follower = %(email)s;""", {'email': email})
	if not following_list:
		return list()
	return following_list[0]

def get_subscribed_threads_list(email):
	subscriptions_list = db.execute("""SELECT thread FROM Subscription
		WHERE subscriber = %(email)s;""", {'email': email})
	result = list()
	for thread in subscriptions_list:
		result.append(thread[0])
	return result

def get_subscribed_user_list(thread):
	user_list = db.execute("""SELECT subscriber FROM Subscription
		WHERE thread = %(thread)s;""", {'thread': thread})
	result = list()
	for user in user_list:
		print(user[0])
		result.append(get_user_dict(user[0]).get('id'))
	return result

def get_subscription(user, thread):
	subscriptions_list = db.execute("""SELECT thread, subscriber FROM Subscription
		WHERE subscriber = %(user)s AND thread = %(thread)s;""", {'user': user,'thread': thread})
	if not subscriptions_list:
		return list()
	subscriptions_list = subscriptions_list[0]
	return {'thread': str_to_json(subscriptions_list[0]),
			'user': str_to_json(subscriptions_list[1])}