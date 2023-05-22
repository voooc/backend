#!/usr/bin/python
# -*- coding:utf-8 -*-
from django.urls import include, path
from . import views
from backend.utils import routers
router = routers.AdminRouter()
router.register(r'article', views.ArticleView, basename="article")
router.register(r'category', views.CategoryView, basename='category')
router.register(r'tag', views.TagView, basename='tag')
router.register(r'discussion', views.DiscussionView, basename='discussion')
router.register(r'comment', views.UserComment, basename='comment')
urlpatterns = [
  path('upload', views.UploadImageAPIView.as_view(), name='upload_image'),
  path('like', views.LikeView.as_view(), name='like'),
  path('comment', views.CommentView.as_view(), name='comment'),
  path('', include(router.urls)),
]