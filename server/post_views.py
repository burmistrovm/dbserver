from django.http import HttpResponse, Http404, HttpRequest
import requests
import json, MySQLdb
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from common import db, MYSQL_DUPLICATE_ENTITY_ERROR
from common import get_post_by_id, get_forum_dict, get_user_dict, get_thread_dict, add_post_to_thread,get_post_list
max1 = 4


@csrf_exempt
def create(request):
	post = json.loads(request.body)
	date = post.get('date')
	thread = post.get('thread')
	message = post.get('message')
	user = post.get('user')
	forum = post.get('forum')
	isDeleted = post.get('isDeleted', False)
	isSpam = post.get('isSpam',False)
	isEdited = post.get('isEdited', False)
	isHighlighted = post.get('isHighlighted', False)
	isApproved = post.get('isApproved', False)
	parent = post.get('parent')
	mpath = ""
	sql = """INSERT INTO Post (date, thread, forum, message, user, isSpam, isDeleted, isEdited, isApproved, isHighlighted, parent, mpath) VALUES \
		(%(date)s, %(thread)s, %(forum)s, %(message)s, %(user)s, %(isSpam)s, %(isDeleted)s, %(isEdited)s, %(isApproved)s, %(isHighlighted)s, %(parent)s, %(mpath)s);"""
	args = {'date': date, 'thread': thread, 'forum': forum, 'message': message, 'user': user, 
	'isSpam': isSpam, 'isDeleted': isDeleted, 'isEdited': isEdited, 'isApproved': isApproved, 'isHighlighted': isHighlighted, 'parent': parent, 'mpath': mpath}
	postID = db.execute(sql, args, True)
	add_post_to_thread(thread)
	if parent == None:
		mpath = mpath + date + '-' + str(postID)
	else:
		mpath_que = db.execute("""SELECT mpath FROM Post \
		WHERE post = %(parent)s;""", {'parent': parent})
		print(mpath_que[0][0])
		mpath = mpath_que[0][0] + "." + str(date) + '-' + str(postID)
	db.execute("""UPDATE Post SET mpath = %(mpath)s WHERE post = %(id)s;""", {'mpath': mpath,'id':postID})
	post = get_post_by_id(postID)
	return JsonResponse({"code": 0, "response": post})

@csrf_exempt
def details(request):
	post = request.GET.get('post')
	if not post: 
		return JsonResponse({"code": 2, "response": "No 'post' key"})
	post_dict = get_post_by_id(post)
	if type(post_dict) == type([]):
		return JsonResponse({"code": 1, "response": "Empty set"})
	user = post_dict.get('user')
	forum = post_dict.get('forum')
	thread = post_dict.get('thread')
	post_dict['user'] = get_user_dict(user)
	post_dict['forum'] = get_forum_dict(forum)
	post_dict['thread'] = get_thread_dict(thread)
	return JsonResponse({"code": 0, "response": post_dict})

@csrf_exempt
def list(request):
	thread = request.GET.get('thread')
	forum = request.GET.get('forum')
	since = request.GET.get('since')
	limit = request.GET.get('limit')
	order = request.GET.get('order')
	sort = request.GET.get('sort')
	if sort == None:
		sort = "flat"
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
	post_list = get_post_list(thread = thread,forum = forum,since = since,order = order,limit = limit,sort = sort)
	for post_dict in post_list:
		if userRelated:
			post_dict['user'] = get_user_dict(post_dict['user'])
		if forumRelated:
			post_dict['forum'] = get_forum_dict(post_dict['forum'])
		if threadRelated:
			post_dict['thread'] = get_thread_dict(post_dict['thread'])
	return JsonResponse({"code": 0, "response": post_list})

@csrf_exempt
def remove(request):
	post_query = json.loads(request.body)
	postID = post_query.get('post')
	post = get_post_by_id(postID)
	thread_id = post['thread']
	db.execute("""UPDATE Post SET isDeleted = 1 WHERE post = %(post)s;""", {'post': postID}, True)
	db.execute("""UPDATE Thread SET posts = posts - 1 WHERE thread = %(thread)s;""", {'thread': thread_id}, post=True)
	return JsonResponse({"code": 0, "response": {"post": postID}})

@csrf_exempt
def restore(request):
	post_query = json.loads(request.body)
	postID = post_query.get('post')
	post = get_post_by_id(postID)
	thread_id = post['thread']
	db.execute("""UPDATE Post SET isDeleted = 0 WHERE post = %(post)s;""", {'post': postID}, True)
	db.execute("""UPDATE Thread SET posts = posts + 1 WHERE thread = %(thread)s;""", {'thread': thread_id}, post=True)
	return JsonResponse({"code": 0, "response": {"post": postID}})

@csrf_exempt
def update(request):
	post_query = json.loads(request.body.decode("utf-8"))
	post_ID = int(post_query.get('post'))
	message = post_query.get('message')
	args = {'post': post_ID, 'message': message}
	db.execute("""UPDATE Post SET message = %(message)s WHERE post = %(post)s;""", args, True)
	post_dict = get_post_by_id(post_ID)
	return JsonResponse({"code": 0, "response": post_dict})

@csrf_exempt
def vote(request):
	voteBody = json.loads(request.body)
	post = voteBody.get('post')
	vote = voteBody.get('vote')
	if vote == 1:
		db.execute("""UPDATE Post SET likes = likes + 1, points = points + 1 WHERE post = %(post)s;""",
				   {'post': post}, True)
	elif vote == -1:
		db.execute("""UPDATE Post SET dislikes = dislikes + 1, points = points - 1 WHERE post = %(post)s;""",
				   {'post': post}, True)
	post_dict = get_post_by_id(post)
	return JsonResponse({"code": 0, "response": post_dict})