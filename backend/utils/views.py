from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from backend.utils.swagger_schema import OperationIDAutoSchema


class MultipleDestroyMixin:
    """
    自定义批量删除mixin
    """
    swagger_schema = OperationIDAutoSchema

    class MultipleDeleteSerializer(serializers.Serializer):
        ids = serializers.ListField(required=True, write_only=True)

    def validate_ids(self, delete_ids):
        # 验证object传入的删除id列表
        if not delete_ids:
            raise ValidationError('参数错误,ids为必传参数')
        if not isinstance(delete_ids, list):
            raise ValidationError('ids格式错误,必须为List')
        queryset = self.get_queryset()
        del_queryset = queryset.filter(id__in=delete_ids)
        if len(delete_ids) != del_queryset.count():
            raise ValidationError('删除数据不存在')
        return del_queryset

    @swagger_auto_schema(request_body=MultipleDeleteSerializer)
    def multiple_delete(self, request, *args, **kwargs):
        delete_ids = request.data.get('ids')
        del_queryset = self.validate_ids(delete_ids)
        del_queryset.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
