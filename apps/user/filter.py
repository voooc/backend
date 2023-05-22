# -*- coding:utf-8 -*-
from rest_framework.filters import BaseFilterBackend
from django.contrib.contenttypes.models import ContentType
from article.models import Like, Comment


class LikeFilterBackend(BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        user = request.GET.get('user')
        type = request.GET.get('type')
        second_type = request.GET.get('second_type')
        if user:
            user = user.replace('-', '')
            like_id = Like.objects.filter(object_type_id=ContentType.objects.get(model=type).id).values_list('id', flat=True)
            queryset = queryset.filter(user_id__id__contains=user).filter(likes_id__id__in=list(like_id))
            if type == 'comment':
                # 如果是评论，二次过滤，判断点赞的是文章评论，还是讨论区的评论
                comment_id = Comment.objects.filter(object_type_id=ContentType.objects.get(model=second_type).id).values_list('id', flat=True)
                like_id = Like.objects.filter(object_id__in=list(comment_id))
                queryset = queryset.filter(likes_id__id__in=list(like_id))
        return queryset
