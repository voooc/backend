#!/usr/bin/python
# -*- coding:utf-8 -*-
from django.urls import include, path
from . import views
from backend.utils import routers
router = routers.AdminRouter()
router.register(r'news', views.NewsViewSet, basename="news")
router.register(r'banner', views.BannerViewSet, basename="banner")
router.register(r'announcement', views.AnnouncementViewSet, basename="announcement")
router.register(r'awards', views.AwardsViewSet, basename='awards')
urlpatterns = [
  path('', include(router.urls)),
]