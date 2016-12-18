from django.http import HttpResponse, Http404, HttpRequest
import requests
import json, MySQLdb
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from common import db, MYSQL_DUPLICATE_ENTITY_ERROR, get_user_dict,get_followers_list,get_following_list,get_subscribed_threads_list,get_post_list
from django.db import connection, DatabaseError, IntegrityError

@csrf_exempt
def create(request):
	user = json.loads(request.body.decode("utf-8"))
	email = user.get('email')
	username = user.get('username')
	name = user.get('name')
	about = user.get('about')
	isAnonymous = user.get('isAnonymous', False)
	sql = """INSERT INTO User (username, about, name, email, isAnonymous) VALUES \
		(%(username)s, %(about)s, %(name)s, %(email)s, %(isAnonymous)s);"""
	args = {'username': username, 'about': about, 'name': name, 'email': email, 'isAnonymous': isAnonymous}
	try:
		ID = db.execute(sql, args, True)
	except IntegrityError:
		return JsonResponse({"code": 5,
							   "response": "This user already exists"})
	except DatabaseError:
		return JsonResponse({"code": 4,
						   "response": "Oh, we have some really bad error"})
	#user_dict = get_user_dict(email)
	return JsonResponse({"code": 0, "response":{'id': ID,
												'email': email,
												'name': name,
												'username': username,
												'isAnonymous': isAnonymous,
												'about': about}})

@csrf_exempt
def details(request):
	email = request.GET.get('user')
	if not email:
		return JsonResponse({"code": 2, "response": "No 'user' key"})
	user_dict = get_user_dict(email)
	user_dict['followers'] = get_followers_list(email)
	user_dict['following'] = get_following_list(email)
	user_dict['subscriptions'] = get_subscribed_threads_list(email)
	return JsonResponse({"code": 0, "response": user_dict, "email": email})

@csrf_exempt
def follow(request):
	follow = json.loads(request.body.decode("utf-8"))
	follower = follow.get('follower')
	followee = follow.get('followee')
	db.execute("""INSERT INTO Follower (follower, followee) VALUES \
		(%(follower)s, %(followee)s);""", {'follower': follower, 'followee': followee})
	user_dict = get_user_dict(follower)
	user_dict['followers'] = get_followers_list(follower)
	user_dict['following'] = get_following_list(follower)
	user_dict['subscriptions'] = get_subscribed_threads_list(follower)
	return JsonResponse({"code": 0, "response": user_dict})

@csrf_exempt
def listFollowers(request):
	email = request.GET.get('user')
	if not email:
		return JsonResponse({"code": 2, "response": "No 'user' key"})
	followers = get_followers_list(email)
	followers_list = list()
	for follower in followers:
		curr_follower = get_user_dict(follower)
		curr_follower['followers'] = get_followers_list(follower)
		curr_follower['following'] = get_following_list(follower)
		curr_follower['subscriptions'] = get_subscribed_threads_list(follower)
		followers_list.append(curr_follower)
	return JsonResponse({"code": 0, "response": followers_list})

@csrf_exempt
def listFollowing(request):
	email = request.GET.get('user')
	if not email:
		return JsonResponse({"code": 2, "response": "No 'user' key"})
	followees = get_following_list(email)
	followings_list = list()
	for followee in followees:
		curr_followee = get_user_dict(followee)
		curr_followee['followers'] = get_followers_list(followee)
		curr_followee['following'] = get_following_list(followee)
		curr_followee['subscriptions'] = get_subscribed_threads_list(followee)
		followings_list.append(curr_followee)
	return JsonResponse({"code": 0, "response": followings_list})

@csrf_exempt
def listPosts(request):
	user = request.GET.get('user')
	since = request.GET.get('since')
	limit = request.GET.get('limit')
	order = request.GET.get('order')
	post_list = get_post_list(user=user,since=since,order=order,limit=limit)
	#return JsonResponse({"code": 0, "response": post_list})
	return JsonResponse({"code": 0, "response": post_list})

@csrf_exempt
def unfollow(request):
	follow = json.loads(request.body.decode("utf-8"))
	follower = follow.get('follower')
	followee = follow.get('followee')
	args = {'follower': follower, 'following': followee}
	db.execute("""DELETE FROM Follower WHERE follower = %(follower)s AND followee = %(following)s;""", args, True)
	user_dict = get_user_dict(follower)
	user_dict['followers'] = get_followers_list(follower)
	user_dict['following'] = get_following_list(follower)
	user_dict['subscriptions'] = get_subscribed_threads_list(follower)
	return JsonResponse({"code": 0, "response": user_dict})

@csrf_exempt
def updateProfile(request):
	user = json.loads(request.body.decode("utf-8"))
	email = user.get('user')
	name = user.get('name')
	about = user.get('about')
	args = {'about': about, 'name': name, 'email': email}
	db.execute("""UPDATE User SET about = %(about)s, name = %(name)s WHERE email = %(email)s;""", args, True)
	user_dict = get_user_dict(email)
	return JsonResponse({"code": 0, "response": user_dict})