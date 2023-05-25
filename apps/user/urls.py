#!/usr/bin/python
# -*- coding:utf-8 -*-
from . import views
from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token
from django.urls import include, re_path, path
from backend.utils import routers

router = routers.AdminRouter()
router.register(r'departments', views.DepartmentsViewSet, basename="departments")  # 部门管理
router.register(r'roles', views.RoleViewSet, basename='roles')
router.register(r'message', views.UseMessage, basename='message')
router.register(r'user', views.UserView, basename='user')
router.register(r'follow', views.UserFollow, basename='follow')
router.register(r'like', views.UserLike, basename='like')
router.register(r'verify', views.VeifyUserViewSet, basename='veify')
urlpatterns = [
    path('retrieve', views.Retrieve.as_view(), name='retrieve'),  # 忘记密码
    path('sing_email', views.ResetUserView.as_view(), name='sing_email'),  # 更换邮箱验证码
    path('email_update', views.EmailView.as_view(), name='email_update'),  # 更换邮箱
    path('retrieve_email', views.RetrieveEmail.as_view(), name='retrieve_email'),  # 忘记密码验证码
    path('login', views.Login.as_view(), name='index'),
    path('register', views.Register.as_view(), name='register'),
    path('register_email', views.RegisterEmail.as_view(), name='register_email'),
    path('logout', views.LogoutAPIView.as_view(), name='logout'),
    path('info', views.UserInfoView.as_view(), name='info'),
    path('user_total', views.UserTotalCountView.as_view(), name='user_total'),
    re_path(r'api/login/$', obtain_jwt_token),  # jwt认证
    re_path(r'^api-token-refresh/', refresh_jwt_token),  # jwt刷新
    path('', include(router.urls)),
]