from backend.utils.permissions import IsAdminOrReadOnly
from news.models import News, Banner, Announcement, Awards
from news.serializers import NewsSerializer, BannerSerializer, NewsRetrieveSerializer, AnnouncementSerializer, AwardsSerializer
from rest_framework.response import Response
from rest_framework import viewsets, status
from django.conf import settings


class NewsViewSet(viewsets.ModelViewSet):
    queryset = News.objects.all().order_by('-add_time')
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = self.queryset.all()
        # 获取请求参数中的排序字段
        show = self.request.query_params.get('show')
        if show:
            queryset.filter(is_published=True)
        else:
            queryset.filter(is_published=False)
        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return NewsRetrieveSerializer
        else:
            return NewsSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        news = News.objects.filter(id=serializer.data['id'])
        url = settings.HOST + 'news/' + str(serializer.data['id'])
        news.update(url=url)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        queryset = self.filter_queryset(self.get_queryset())
        # 获取前一篇文章
        previous = queryset.filter(id__lt=instance.id).order_by('-id').first()
        previous_id = {'id': previous.id, 'title': previous.title} if previous else None

        # 获取后一篇文章
        next = queryset.filter(id__gt=instance.id).order_by('id').first()
        next_id = {'id': next.id, 'title': next.title} if next else None

        response = serializer.data
        response['previous'] = previous_id
        response['next'] = next_id
        return Response(response)


class AnnouncementViewSet(viewsets.ModelViewSet):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer
    permission_classes = [IsAdminOrReadOnly]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_200_OK)


class BannerViewSet(viewsets.ModelViewSet):
    queryset = Banner.objects.all().order_by('order')
    serializer_class = BannerSerializer
    permission_classes = [IsAdminOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_200_OK)


class AwardsViewSet(viewsets.ModelViewSet):
    queryset = Awards.objects.all()
    serializer_class = AwardsSerializer
    permission_classes = [IsAdminOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_200_OK)
