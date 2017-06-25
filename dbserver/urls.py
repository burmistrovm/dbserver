"""dbserver URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin
from server import user_views
from server import forum_views
from server import post_views
from server import thread_views
from server import common_functions

user_patterns = [
    url(r'^create/', user_views.create),
    url(r'^details/', user_views.details),
    url(r'^follow/', user_views.follow),
    url(r'^listFollowers/', user_views.listFollowers),
    url(r'^listFollowing/', user_views.listFollowing),
    url(r'^listPosts/', user_views.listPosts),
    url(r'^unfollow/', user_views.unfollow),
    url(r'^updateProfile/', user_views.updateProfile),
]

forum_patterns = [
    url(r'^create/', forum_views.create),
    url(r'^details/', forum_views.details),
    url(r'^listPosts/', forum_views.listPosts),
    url(r'^listThreads/', forum_views.listThreads),
    url(r'^listUsers/', forum_views.listUsers),
]

thread_patterns = [
    url(r'^close/', thread_views.close),
    url(r'^create/', thread_views.create),
    url(r'^details/', thread_views.details),
    url(r'^list/', thread_views.list),
    url(r'^listPosts/', thread_views.listPosts),
    url(r'^open/', thread_views.open),
    url(r'^remove/', thread_views.remove),
    url(r'^restore/', thread_views.restore),
    url(r'^subscribe/', thread_views.subscribe),
    url(r'^unsubscribe/', thread_views.unsubscribe),
    url(r'^update/', thread_views.update),
    url(r'^vote/', thread_views.vote),
]

post_patterns = [
    url(r'^create/', post_views.create),
    url(r'^details/', post_views.details),
    url(r'^list/', post_views.list),
    url(r'^remove/', post_views.remove),
    url(r'^restore/', post_views.restore),
    url(r'^update/', post_views.update),
    url(r'^vote/', post_views.vote),
]

urlpatterns = [
    url(r'^db/api/status/', common_functions.status),
    url(r'^db/api/clear/', common_functions.clear),
    url(r'^db/api/user/',include(user_patterns)),
    url(r'^db/api/forum/',include(forum_patterns)),
    url(r'^db/api/thread/',include(thread_patterns)),
    url(r'^db/api/post/',include(post_patterns)),
]
