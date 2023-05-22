# -*- coding:utf-8 -*-
from rest_framework.filters import BaseFilterBackend
from django.db.models import Q


class ArticleFilterBackend(BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        category = request.GET.get('category')
        tag = request.GET.get('tag')
        title = request.GET.get('title')
        user = request.GET.get('user')
        if user:
            user = user.replace('-', '')
            queryset = queryset.filter(author_id__id__contains=user)
            return queryset
        if tag:
            tag = tag.split(',')
        if category:
            queryset = queryset.filter(category_id__id__contains=category)
            return queryset
        if tag:
            queryset = queryset.filter(tags__in=tag)
            return queryset
        if title:
            queryset = queryset.filter(title__icontains=title)
            return queryset
        if category and tag:
            queryset = queryset.filter(Q(category_id__id__icontains=category)|Q(tags__in=tag))
        return queryset
