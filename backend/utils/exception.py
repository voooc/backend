from rest_framework.views import exception_handler
from rest_framework.views import Response
from rest_framework import status
from .logger import log					# 自定义的日志记录使用方法


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    log.error('view是：%s ，错误是%s' % (context['view'].__class__.__name__, str(exc)))
    print(context['view'].__class__.__name__)
    if response is None:
        return Response({
            'message': '服务器错误:{exc}'.format(exc=exc),
            'code': -1,
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR, exception=True)

    else:
        return Response({
            'message': '服务器错误:{exc}'.format(exc=exc),
            'code': -1,
        }, status=response.status_code, exception=True)