from django.http import HttpResponse, Http404, HttpRequest
import requests
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from common_functions import execute
from common_functions import get_post_by_id,get_post_dict, get_forum_dict, get_user_dict, get_thread_by_id, add_post_to_thread,get_post_list
from django.db import DatabaseError, IntegrityError
import time

@csrf_exempt
def create(request):
	begin = time.time()
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
	try:
		postID = execute(sql, args, True)
	except IntegrityError:
		post_dict = get_post_dict(user, date)
		return JsonResponse({"code": 0, "response": post_dict})
	except DatabaseError:
		return JsonResponse({"code": 4,
						   "response": "Oh, we have some really bad error"})
	add_post_to_thread(thread)
	if parent == None:
		mpath = mpath + date + '-' + str(postID)
	else:
		mpath_que = execute("""SELECT mpath FROM Post \
		WHERE post = %(parent)s;""", {'parent': parent})
		mpath = mpath_que[0][0] + "." + str(date) + '-' + str(postID)
	execute("""UPDATE Post SET mpath = %(mpath)s WHERE post = %(id)s;""", {'mpath': mpath,'id':postID})
	#post = get_post_by_id(postID)
	print(request.get_full_path() + request.body + "-")
	print((time.time()-begin)*1000)
	return JsonResponse({"code": 0, "response":{'id': postID,
												'user': user,
												'thread': thread,
												'forum': forum,
												'message': message,
												'parent': parent,
												'date': date,
												'isSpam': isSpam,
												'isEdited': isEdited,
												'isDeleted': isDeleted,
												'isHighlighted': isHighlighted,
												'isApproved': isApproved}})

@csrf_exempt
def details(request):
	begin = time.time()
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
	post_dict['thread'] = get_thread_by_id(thread)
	print(request.get_full_path() + request.body + "-")
	print((time.time()-begin)*1000)
	return JsonResponse({"code": 0, "response": post_dict})

@csrf_exempt
def list(request):
	begin = time.time()
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
	post_list = get_post_list(thread = thread,forum = forum,since = since,order = order,limit = limit,sort = sort,relations = relations)
	print(request.get_full_path() + request.body + "-")
	print((time.time()-begin)*1000)
	return JsonResponse({"code": 0, "response": post_list})

@csrf_exempt
def remove(request):
	post_query = json.loads(request.body)
	postID = post_query.get('post')
	post = get_post_by_id(postID)
	thread_id = post['thread']
	execute("""UPDATE Post SET isDeleted = 1 WHERE post = %(post)s;""", {'post': postID}, True)
	execute("""UPDATE Thread SET posts = posts - 1 WHERE thread = %(thread)s;""", {'thread': thread_id}, post=True)
	return JsonResponse({"code": 0, "response": {"post": postID}})

@csrf_exempt
def restore(request):
	post_query = json.loads(request.body)
	postID = post_query.get('post')
	post = get_post_by_id(postID)
	thread_id = post['thread']
	execute("""UPDATE Post SET isDeleted = 0 WHERE post = %(post)s;""", {'post': postID}, True)
	execute("""UPDATE Thread SET posts = posts + 1 WHERE thread = %(thread)s;""", {'thread': thread_id}, post=True)
	return JsonResponse({"code": 0, "response": {"post": postID}})

@csrf_exempt
def update(request):
	post_query = json.loads(request.body.decode("utf-8"))
	post_ID = int(post_query.get('post'))
	message = post_query.get('message')
	args = {'post': post_ID, 'message': message}
	execute("""UPDATE Post SET message = %(message)s WHERE post = %(post)s;""", args, True)
	post_dict = get_post_by_id(post_ID)
	return JsonResponse({"code": 0, "response": post_dict})

@csrf_exempt
def vote(request):
	begin = time.time()
	voteBody = json.loads(request.body)
	post = voteBody.get('post')
	vote = voteBody.get('vote')
	if vote == 1:
		execute("""UPDATE Post SET likes = likes + 1, points = points + 1 WHERE post = %(post)s;""",
				   {'post': post}, True)
	elif vote == -1:
		execute("""UPDATE Post SET dislikes = dislikes + 1, points = points - 1 WHERE post = %(post)s;""",
				   {'post': post}, True)
	post_dict = get_post_by_id(post)
	print(request.get_full_path() + request.body + "-")
	print((time.time()-begin)*1000)
	return JsonResponse({"code": 0, "response": post_dict})