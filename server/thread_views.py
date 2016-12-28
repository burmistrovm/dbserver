from django.http import HttpResponse, Http404, HttpRequest
import requests
import json, MySQLdb
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import connection, DatabaseError, IntegrityError
from common import db, MYSQL_DUPLICATE_ENTITY_ERROR, get_thread_dict, get_user_dict, get_forum_dict,get_thread_by_id,get_subscription,get_post_list,get_thread_list
import time

@csrf_exempt
def open(request):
	thread_query = json.loads(request.body.decode("utf-8"))
	thread = int(thread_query.get('thread'))
	db.execute("""UPDATE Thread SET isClosed = False WHERE thread = %(thread)s;""", {'thread': thread}, True)
	return JsonResponse({"code": 0, "response": thread})

@csrf_exempt
def close(request):
	thread_query = json.loads(request.body.decode("utf-8"))
	thread = int(thread_query.get('thread'))
	db.execute("""UPDATE Thread SET isClosed = True WHERE thread = %(thread)s;""", {'thread': thread}, True)
	return JsonResponse({"code": 0, "response": thread})


@csrf_exempt
def create(request):
	thread = json.loads(request.body.decode("utf-8"))
	title = thread.get('title')
	user = thread.get('user')
	forum = thread.get('forum')
	message = thread.get('message')
	date = thread.get('date')
	slug = thread.get('slug')
	if thread.get('isClosed'):
		isClosed = True
	else:
		isClosed = False
	if thread.get('isDeleted', False):
		isDeleted = True
	else:
		isDeleted = False
	sql = """INSERT INTO Thread (title, user, forum, message, date, slug, isDeleted, isClosed) VALUES \
		(%(title)s, %(user)s, %(forum)s, %(message)s, %(date)s, %(slug)s, %(isDeleted)s, %(isClosed)s);"""
	args = {'title': title, 'user': user, 'forum': forum, 'message': message, 'date': date, 
	'slug': slug, 'isDeleted': isDeleted, 'isClosed': isClosed}
	try:
		thread_id = db.execute(sql, args, True)
	except IntegrityError:
		thread_dict = get_thread_dict(title)
		return JsonResponse({"code": 0, "response": thread_dict})
	except DatabaseError:
		return JsonResponse({"code": 4,
						   "response": "Oh, we have some really bad error"})
	thread_dict = get_thread_by_id(thread_id)
	return JsonResponse({"code": 0, "response": thread_dict})

@csrf_exempt
def details(request):
	thread = int(request.GET.get('thread'))
	related = request.GET.getlist('related')
	relations = []
	relations.extend(related)
	threadRelated = False
	forumRelated = False
	userRelated = False
	for related_value in relations:
		if related_value == "forum":
			forumRelated = True
		elif related_value == "user":
			userRelated = True
		else:
			return JsonResponse({"code": 3, "response": "Wrong related value"})
	if not thread: 
		return JsonResponse({"code": 2, "response": "No 'thread' key"})
	thread_dict = get_thread_by_id(thread)
	user = thread_dict.get('user')
	forum = thread_dict.get('forum')
	thread_dict['user'] = get_user_dict(user)
	thread_dict['forum'] = get_forum_dict(forum)
	return JsonResponse({"code": 0, "response": thread_dict})

@csrf_exempt
def list(request):
	thread = int(request.GET.get('thread'))
	user = request.GET.get('user')
	forum = request.GET.get('forum')
	since = request.GET.get('since')
	limit = request.GET.get('limit')
	order = request.GET.get('order')
	related = request.GET.getlist('related')
	relations = []
	relations.extend(related)
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
	thread_list = get_thread_list(user = user,forum = forum,since = since,order = order,limit = limit)
	for thread_dict in thread_list:
		if userRelated:
			thread_dict['user'] = get_user_dict(thread_dict['user'])
		if forumRelated:
			thread_dict['forum'] = get_forum_dict(post_dict['forum'])
	return JsonResponse({"code": 0, "response": thread_list})

@csrf_exempt
def listPosts(request):
	begin = time.time()
	thread = request.GET.get('thread')
	since = request.GET.get('since')
	limit = request.GET.get('limit')
	order = request.GET.get('order')
	sort = request.GET.get('sort')
	if sort == None:
		sort = "flat"
	related = request.GET.getlist('related')
	relations = []
	relations.extend(related)
	post_list = get_post_list(thread = thread,since = since,order = order,limit = limit,sort = sort,relations = relations)
	print(request.get_full_path() + request.body + "-")
	print((time.time()-begin)*1000)
	return JsonResponse({"code": 0, "response": post_list})

@csrf_exempt
def remove(request):
	thread_query = json.loads(request.body)
	thread_ID = thread_query.get('thread')
	db.execute("""UPDATE Post SET isDeleted = 1 WHERE thread = '%(thread)s';""", {'thread': thread_ID}, True)
	db.execute("""UPDATE Thread SET posts = 0, isDeleted = True WHERE thread = %(thread)s;""", {'thread': thread_ID}, True)
	return JsonResponse({"code": 0, "response": {"thread": thread_ID}})

@csrf_exempt
def restore(request):
	thread_query = json.loads(request.body)
	thread_ID = thread_query.get('thread')
	db.execute("UPDATE Post SET isDeleted = False WHERE thread = '{thread}';".format(thread = str(thread_ID) + ""),{}, True)
	posts = int(db.execute("SELECT COUNT(*) FROM Post WHERE thread = '{thread}';".format(thread = str(thread_ID) + ""))[0][0])
	db.execute("""UPDATE Thread SET posts = %(posts)s, isDeleted = False WHERE thread = %(thread)s;""", {'posts':posts,'thread': thread_ID}, True)
	return JsonResponse({"code": 0, "response": {"thread": thread_ID}})

@csrf_exempt
def subscribe(request):
	subscription = json.loads(request.body.decode("utf-8"))
	user = subscription.get('user')
	thread = subscription.get('thread')
	try:
		subscription_id = db.execute("""INSERT INTO Subscription (subscriber, thread) VALUES \
			(%(user)s, %(thread)s);""", {'user': user, 'thread': thread}, True)
	except IntegrityError:
		1
	subscription_dict = get_subscription(user, thread)
	return JsonResponse({"code": 0, "response": subscription_dict})

@csrf_exempt
def unsubscribe(request):
	subscription = json.loads(request.body.decode("utf-8"))
	user = subscription.get('user')
	thread =subscription.get('thread')
	subscription_id = db.execute("""DELETE FROM Subscription WHERE subscriber = %(subscriber)s AND thread = %(thread)s;""",
		   {'subscriber': user, 'thread': thread}, True)
	return JsonResponse({"code": 0, "response": {'thread': thread, 'user': user}})

@csrf_exempt
def update(request):
	up_thread = json.loads(request.body.decode("utf-8"))
	thread = up_thread.get('thread')
	message = up_thread.get('message')
	slug = up_thread.get('slug')
	args = {'thread': thread, 'message': message, 'slug': slug}
	db.execute("""UPDATE Thread SET message = %(message)s, slug = %(slug)s WHERE thread = %(thread)s;""", args, True)
	thread_dict = get_thread_by_id(thread)
	return JsonResponse({"code": 0, "response": thread_dict})

@csrf_exempt
def vote(request):
	voteBody = json.loads(request.body)
	thread = voteBody.get('thread')
	vote = voteBody.get('vote')
	if vote == 1:
		db.execute("""UPDATE Thread SET likes = likes + 1, points = points + 1 WHERE thread = %(thread)s;""",
				   {'thread': thread}, True)
	elif vote == -1:
		db.execute("""UPDATE Thread SET dislikes = dislikes + 1, points = points - 1 WHERE thread = %(thread)s;""",
				   {'thread': thread}, True)
	thread_dict = get_thread_by_id(thread)
	return JsonResponse({"code": 0, "response": thread_dict})