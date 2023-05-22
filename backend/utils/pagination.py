from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class GlobalPagination(PageNumberPagination):
    page_query_param = 'page'  # 前端发送的页数关键字名，默认为page
    page_size = 10  # 每页数目
    page_size_query_param = 'pageSize'  # 前端发送的每页数目关键字名，默认为None
    max_page_size = 1000  # 前端最多能设置的每页数量

    def get_paginated_response(self, data):
        return Response({
            'total': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'items': data
        })
