# -*- coding: utf-8 -*-
from django.http import HttpResponse, Http404, HttpRequest
import requests
import MySQLdb
import json 
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from common import db, MYSQL_DUPLICATE_ENTITY_ERROR, get_forum_dict,get_user_dict,get_post_list,get_thread_dict,get_thread_list,get_user_list

@csrf_exempt
def create(request):
	forum = json.loads(request.body)
	name = forum.get('name')
	short_name = forum.get('short_name')
	user = forum.get('user')
	sql = """INSERT INTO Forum (name, short_name, user) VALUES \
		(%(name)s, %(short_name)s, %(user)s);"""
	args = {'name': name, 'short_name': short_name, 'user': user}
	try:
		db.execute(sql, args, True)
	except MySQLdb.IntegrityError, message:
		print message[0]
	finally:
		forum_dict = get_forum_dict(short_name)
		return JsonResponse({"code": 0, "response": forum_dict})

@csrf_exempt
def details(request):
	short_name = request.GET.get('forum')
	if not short_name:
		return JsonResponse({"code": 2, "response": "No 'forum' key"})
	forum_dict = get_forum_dict(short_name)
	if not forum_dict:
		return JsonResponse({"code": 1, "response": "Empty set"})
	email = forum_dict.get('user')
	user = get_user_dict(email)
	forum_dict.update({'user': user})
	return JsonResponse({"code": 0, "response": forum_dict})

@csrf_exempt
def listPosts(request):
	forum = request.GET.get('forum')
	since = request.GET.get('since')
	limit = request.GET.get('limit')
	order = request.GET.get('order')
	related = request.GET.getlist('related')
	relations = list()
	if type(related) is list:
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
	post_list = get_post_list(forum = forum,since = since,order = order,limit = limit)
	for post_dict in post_list:
		if userRelated:
			post_dict['user'] = get_user_dict(post_dict['user'])
		if forumRelated:
			post_dict['forum'] = get_forum_dict(post_dict['forum'])
		if threadRelated:
			post_dict['thread'] = get_thread_dict(post_dict['thread'])
	return JsonResponse({"code": 0, "response": post_list})

@csrf_exempt
def listThreads(request):
	forum = request.GET.get('forum')
	limit = request.GET.get('limit')
	order = request.GET.get('order')
	since = request.GET.get('since')
	related = request.GET.getlist('related')
	relations = list()
	if type(related) is list:
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
	thread_list = get_thread_list(forum = forum, order = order,limit = limit,since = since)
	for thread_dict in thread_list:
		if userRelated:
			thread_dict['user'] = get_user_dict(thread_dict['user'])
		if forumRelated:
			thread_dict['forum'] = get_forum_dict(thread_dict['forum'])
		if threadRelated:
			thread_dict['thread'] = get_thread_dict(thread_dict['thread'])
	return JsonResponse({"code": 0, "response": thread_list})

@csrf_exempt
def listUsers(request):
	forum = request.GET.get('forum')
	limit = request.GET.get('limit')
	order = request.GET.get('order')
	related = request.GET.getlist('related')
	relations = list()
	if type(related) is list:
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
	user_list = get_user_list(forum = forum, order = order,limit = limit)
	return JsonResponse({"code": 0, "response": user_list})