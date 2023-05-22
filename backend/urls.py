from rest_framework import routers
from django.conf import settings
from django.urls import path, include, re_path
from django.views.decorators.clickjacking import xframe_options_exempt
from drf_yasg import openapi
from rest_framework import permissions
from django.views.static import serve
from drf_yasg.views import get_schema_view
from article.views import ES
schema_view = get_schema_view(
    openapi.Info(
        title="实验室学习系统API",
        default_version='v1.0.0',
        description="实验室学习系统",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

base_api = settings.BASE_API
router = routers.DefaultRouter()
urlpatterns = [
    path(f'{base_api}user/', include('user.urls')),  # 用户模块
    path(f'{base_api}', include('article.urls')),  # 博客模块
    path(f'{base_api}', include('news.urls')),  # 博客模块
	path("index/", ES.as_view(), name="index"),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),  # 配置文件上传html显示,
    re_path(rf'^{base_api}swagger(?P<format>\.json|\.yaml)$',
            xframe_options_exempt(schema_view.without_ui(cache_timeout=0)), name='schema-json'),
    path(f'{base_api}swagger/',
         xframe_options_exempt(schema_view.with_ui('swagger', cache_timeout=0)), name='schema-swagger-ui'),
    path(f'{base_api}redoc/',
         xframe_options_exempt(schema_view.with_ui('redoc', cache_timeout=0)), name='schema-redoc'),
]
