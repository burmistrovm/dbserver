from django.db import connection,transaction
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse


def execute(sql, args=(), post=False):
	cursor = connection.cursor()
	if post:
		cursor.execute(sql, args)
		result = cursor.lastrowid
	else:
		cursor.execute(sql, args)
		result = cursor.fetchall()
	cursor.close()
	return result

@csrf_exempt
def clear(request):
	execute("""TRUNCATE TABLE Forum;""", post=True)
	execute("""TRUNCATE TABLE User;""", post=True)
	execute("""TRUNCATE TABLE Post;""", post=True)
	execute("""TRUNCATE TABLE Thread;""", post=True)
	execute("""TRUNCATE TABLE Subscription;""", post=True)
	execute("""TRUNCATE TABLE Follower;""", post=True)
	return JsonResponse({"code": 0, "response": "OK"})

@csrf_exempt
def status(request):
	user_count = execute("""SELECT count(*) FROM User;""")
	thread_count = execute("""SELECT count(*) FROM Thread;""")
	forum_count = execute("""SELECT count(*) FROM Forum;""")
	post_count = execute("""SELECT count(*) FROM Post;""")
	users = user_count[0][0]
	threads = thread_count[0][0]
	forums = forum_count[0][0]
	posts = post_count[0][0]
	return JsonResponse({"code": 0, "response": {"user": users, "thread": threads, "forum": forums, "post": posts}})

def str_to_json(value, is_bool=False):
	if is_bool:
		return value != 0
	if value == "NULL":
		return None
	return value

def get_user_dict(email):
	user_list_sql = execute("""SELECT user, email, name, username, isAnonymous, about FROM User \
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
	forum_list_sql = execute("""SELECT forum, name, short_name, user FROM Forum \
		WHERE short_name = %(short_name)s;""", {'short_name': short_name})
	if not forum_list_sql:
		return dict()
	forum_sql = forum_list_sql[0]
	return {'id': str_to_json(forum_sql[0]),
			'name': str_to_json(forum_sql[1]),
			'short_name': str_to_json(forum_sql[2]),
			'user': str_to_json(forum_sql[3])}

def get_post_list(user="", thread="", forum="", since="", order="", limit="",sort="flat",relations=[]):
	realated_items_sql = ""
	realated_join_sql = ""
	threadRelated = False
	forumRelated = False
	userRelated = False
	for related_value in relations:
		if related_value == "thread":
			threadRelated = True
		elif related_value == "forum":
			forumRelated = True
		elif related_value == "user":
			userRelated = True
	if thread != "" and thread != None:
		where = "Post.thread = '{}' ".format(thread)

	if user != "" and user != None:
		where = "Post.user = '{}'".format(user)

	elif forum != "" and forum != None:
		where = "Post.forum = '{}' ".format(forum)
		realated_items_sql += """,User.user, User.email, User.name, User.username, User.isAnonymous, User.about"""
		realated_join_sql += """LEFT JOIN User ON(Post.user = email)"""
		realated_items_sql += """,Forum.forum, Forum.name, Forum.short_name, Forum.user"""
		realated_join_sql += """LEFT JOIN Forum ON(Post.forum = Forum.short_name)"""
		realated_items_sql += """,Thread.title, Thread.user, Thread.forum, Thread.message, Thread.date, Thread.slug, Thread.isDeleted,\
		Thread.isClosed, Thread.thread, Thread.posts, Thread.points, Thread.likes, Thread.dislikes"""
		realated_join_sql += """LEFT JOIN Thread ON(Post.thread = Thread.thread)"""

	since_sql = ""
	if since != None:
		since_sql = """AND Post.date >= '{}'""".format(since)
	order_sql = """ORDER BY Post.date """
	if order != None:
		order_sql = order_sql + """{}""".format(order)
	limit_sql = ""
	if limit != None:
		limit_sql = """LIMIT {}""".format(limit)


	if sort == "flat":
		sql = "SELECT Post.post, Post.user, Post.thread, Post.forum, Post.message, Post.parent, Post.date, Post.likes, Post.dislikes, Post.points, \
			Post.isSpam, Post.isEdited, Post.isDeleted, Post.isHighlighted, Post.isApproved, Post.mpath {related_items} FROM Post {realated_join} \
			WHERE {where} {since} {order} {limit};".format(where = where, order = order_sql, since = since_sql, 
				limit = limit_sql,related_items=realated_items_sql,realated_join=realated_join_sql)
		print(sql)
		post_list_sql = execute(sql)

	if sort == "tree":
		sql = "SELECT Post.post, Post.user, Post.thread, Post.forum, Post.message, Post.parent, Post.date, Post.likes, Post.dislikes, Post.points, \
			Post.isSpam, Post.isEdited, Post.isDeleted, Post.isHighlighted, Post.isApproved, Post.mpath {related_items} FROM Post {realated_join} \
			WHERE {where} and parent IS NULL {since} {order} {limit};".format(where = where, order = order_sql, since = since_sql, limit = limit_sql,
				related_items=realated_items_sql,realated_join=realated_join_sql)
		post_parent_list_sql = execute(sql)
		lenght = len(post_parent_list_sql)
		post_list_sql = list()
		for post in post_parent_list_sql:
			parent_mpath = post[15]
			post_child_list_sql = execute(("SELECT Post.post, Post.user, Post.thread, Post.forum, Post.message, Post.parent, Post.date, \
				Post.likes, Post.dislikes, Post.points, Post.isSpam, Post.isEdited, Post.isDeleted, Post.isHighlighted, Post.isApproved, Post.mpath \
				{related_items} FROM Post {realated_join} WHERE {where} AND parent IS NOT NULL AND mpath \
				LIKE '{parent}' ORDER BY Post.mpath, Post.date;").format(where = where,parent = parent_mpath +"%%",related_items=realated_items_sql,realated_join=realated_join_sql))
			post_list_sql.append(post)
			post_list_sql.extend(post_child_list_sql)

	if sort == "parent_tree":
		sql = "SELECT Post.post, Post.user, Post.thread, Post.forum, Post.message, Post.parent, Post.date, Post.likes, Post.dislikes, Post.points, \
			Post.isSpam, Post.isEdited, Post.isDeleted, Post.isHighlighted, Post.isApproved, Post.mpath {related_items} FROM Post {realated_join} \
			WHERE {where} AND Post.parent IS NULL {since} {order} {limit};".format(where = where, order = order_sql, since = since_sql, limit = limit_sql,related_items=realated_items_sql,realated_join=realated_join_sql)
		post_parent_list_sql = execute(sql)
		lenght = len(post_parent_list_sql)
		post_list_sql = list()
		for post in post_parent_list_sql:
			parent_mpath = post[15]
			post_child_list_sql = execute(("SELECT Post.post, Post.user, Post.thread, Post.forum,Post.message, Post.parent, Post.date, Post.likes, Post.dislikes, Post.points, \
			Post.isSpam, Post.isEdited, Post.isDeleted, Post.isHighlighted, Post.isApproved, Post.mpath {related_items} FROM Post {realated_join} \
			WHERE {where} AND Post.parent IS NOT NULL AND Post.mpath LIKE '{parent}' ORDER BY Post.mpath, Post.date;").format(where = where, parent = parent_mpath +"%%",related_items=realated_items_sql,realated_join=realated_join_sql))
			post_list_sql.append(post)
			post_list_sql.extend(post_child_list_sql)
		limit = len(post_list_sql)
	post_list = list()
	if limit == None:
		limit = len(post_list_sql)
	i=0
	while (i < int(limit)) and (i < len(post_list_sql)):
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
		if forum != "" and forum != None:
			if userRelated:
				post_list[i]['user'] = {'id': post_list_sql[i][16],
				'email': post_list_sql[i][17],
				'name': post_list_sql[i][18],
				'username': post_list_sql[i][19],
				'isAnonymous': post_list_sql[i][20],
				'about': post_list_sql[i][21]
				}
			if forumRelated:
				post_list[i]['forum'] = {'id': str_to_json(post_list_sql[i][22]),
				'name': str_to_json(post_list_sql[i][23]),
				'short_name': str_to_json(post_list_sql[i][24]),
				'user': str_to_json(post_list_sql[i][25])}
			if threadRelated:
				post_list[i]['thread'] = {'title': str_to_json(post_list_sql[i][26]),
				'user': str_to_json(post_list_sql[i][27]), 
				'forum': str_to_json(post_list_sql[i][28]), 
				'message': str_to_json(post_list_sql[i][29]), 
				'date': str_to_json(post_list_sql[i][30]).strftime('%Y-%m-%d %H:%M:%S'),
				'slug': str_to_json(post_list_sql[i][31]), 
				'isDeleted': str_to_json(post_list_sql[i][32]), 
				'isClosed': str_to_json(post_list_sql[i][33]),
				'id':str_to_json(post_list_sql[i][34]),
				'posts':str_to_json(post_list_sql[i][35]),
				'points':str_to_json(post_list_sql[i][36]),
				'likes':str_to_json(post_list_sql[i][37]),
				'dislikes': str_to_json(post_list_sql[i][38])}
		i = i+1
	return post_list

def get_thread_list(user="",since="",forum="",limit="",order="ASC"):
	if user != "" and user != None:
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
	thread_list_sql = execute("""SELECT title, user, forum, message, date, slug, isDeleted, isClosed, thread, posts, points, likes, dislikes FROM Thread \
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

def get_user_list(forum,since,limit,order="ASC"):
	since_sql = ""
	if since != None:
		since_sql = """AND u.user >= {}""".format(since)
	order_sql = """ORDER BY name """
	if order != None:
		order_sql = order_sql + """{}""".format(order)
	limit_sql = ""
	if limit != None:
		limit = int(limit)
	else:
		limit = -1
	user_list_sql = execute("""SELECT u.user, email, name, username, isAnonymous, about FROM User AS u \
		INNER JOIN Post AS p ON(p.user = u.email)\
		WHERE forum = '{forum}' {since} {order};""".format(forum = forum, order = order_sql, since = since_sql))
	user_list = list();
	seen = set();
	result = list();
	i = 0
	for x in user_list_sql:
		if x in seen:
			continue
		seen.add(x)
		result.append(x)
		i = i + 1
		if i == limit:
			break
	for user_sql in result:
		user_list.append({'id': str_to_json(user_sql[0]),
			'email': str_to_json(user_sql[1]),
			'name': str_to_json(user_sql[2]),
			'username': str_to_json(user_sql[3]),
			'isAnonymous': str_to_json(user_sql[4], True),
			'about': str_to_json(user_sql[5]),
			'subscriptions': get_subscribed_threads_list(user_sql[1])})
	return user_list;
	

def get_thread_dict(title):
	thread_list_sql = execute("""SELECT title, user, forum, message, date, slug, isDeleted, isClosed, thread, posts, points, likes, dislikes FROM Thread \
		WHERE title = %(title)s LIMIT 1;""", {'title': title})
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
	thread_list_sql = execute("""SELECT title, user, forum, message, date, slug, isDeleted, isClosed, thread, posts, points, likes, dislikes FROM Thread \
		WHERE thread = %(thread)s LIMIT 1;""", {'thread': thread})
	if not thread_list_sql:
		return dict()
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
			'subscriptions': get_subscribed_user_list(thread_sql[8])
			}


def get_post_by_id(postId):
	sql = """SELECT post, user, thread, forum, message, parent, date, likes, dislikes, points, \
		isSpam, isEdited, isDeleted, isHighlighted, isApproved, mpath FROM Post \
		WHERE post = %(id)s LIMIT 1;"""

	post_list_sql = execute(sql, {'id': postId})
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


def get_post_dict(user, date):
	sql = """SELECT post, user, thread, forum, message, parent, date, likes, dislikes, points, \
		isSpam, isEdited, isDeleted, isHighlighted, isApproved, mpath FROM Post \
		WHERE user = %(user)s AND date = %(date)s LIMIT 1;"""

	post_list_sql = execute(sql, {'user':user, 'date':date})
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
	execute("""UPDATE Thread SET posts = posts + 1 WHERE thread = %(thread)s;""", {'thread': thread}, post=True)

def get_followers_list(email):
	follower_list = execute("""SELECT follower FROM Follower
		WHERE followee = %(email)s;""", {'email': email})
	if not follower_list:
		return list()
	return follower_list[0]

def get_following_list(email):
	following_list = execute("""SELECT followee FROM Follower
		WHERE follower = %(email)s;""", {'email': email})
	if not following_list:
		return list()
	return following_list[0]

def get_subscribed_threads_list(email):
	subscriptions_list = execute("""SELECT thread FROM Subscription
		WHERE subscriber = %(email)s;""", {'email': email})
	result = list()
	for thread in subscriptions_list:
		result.append(thread[0])
	return result

def get_subscribed_user_list(thread):
	user_list = execute("""SELECT subscriber FROM Subscription
		WHERE thread = %(thread)s;""", {'thread': thread})
	result = list()
	for user in user_list:
		result.append(get_user_dict(user[0]).get('id'))
	return result

def get_subscription(user, thread):
	subscriptions_list = execute("""SELECT thread, subscriber FROM Subscription
		WHERE subscriber = %(user)s AND thread = %(thread)s;""", {'user': user,'thread': thread})
	if not subscriptions_list:
		return list()
	subscriptions_list = subscriptions_list[0]
	return {'thread': str_to_json(subscriptions_list[0]),
			'user': str_to_json(subscriptions_list[1])}