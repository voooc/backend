from backend.utils.permissions import IsAdminOrReadOnly
from news.models import News, Banner, Announcement, Awards
from news.serializers import NewsSerializer, BannerSerializer, NewsRetrieveSerializer, AnnouncementSerializer, AwardsSerializer
from rest_framework.response import Response
from rest_framework import viewsets, status
from django.conf import settings
from elasticsearch import Elasticsearch
from rest_framework.views import APIView
from elasticsearch.helpers import bulk
from rest_framework.permissions import AllowAny
es = Elasticsearch(["http://127.0.0.1:9200"])


class NewsSearch:
    @staticmethod
    def import_index():
        query_obj = News.objects.all()
        action = [
            {
                "_index": "news",
                "_id": str(i.id),
                '_source': {
                    'es_id': str(i.id),
                    'title': i.title,
                    'content': i.content,
                }
            } for i in query_obj]
        try:
            bulk(es, action, request_timeout=1000)
        except Exception as e:
            print(e)
        print("导入成功")

    @staticmethod
    def filter_msg(search_msg, search_index):
        body = {
            "query": {
                "bool": {
                    "should": [
                        {
                            "match": {
                                "title": search_msg
                            }
                        }, {
                            "match": {
                                "content": search_msg
                            }
                        }
                    ]
                }
            },
            "size": 200,  # 设置最大的返回值
        }
        res = es.search(index=search_index, body=body)
        return res


class ESNews(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        body = {
            "mappings": {
                "properties": {
                    "id": {"type": "long", "index": "false"},
                     "title": {"type": "text", "analyzer": "ik_smart"},
                     "content": {"type": "text", "analyzer": "ik_smart"},
                }
            },
            "settings": {
                "number_of_shards": 2,  # 分片数
                "number_of_replicas": 0  # 副本数
            }
        }
        es.indices.create(index="news", body=body)
        print("索引创建成功")
        return Response('ok')


class NewsViewSet(viewsets.ModelViewSet):
    queryset = News.objects.all().order_by('-add_time')
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = self.queryset.all()
        show = self.request.query_params.get('is_published')
        if show:
            queryset.filter(is_published=True)
        # 获取请求参数中的排序字段
        sort_by = self.request.query_params.get('ordering')
        if sort_by == 'view':
            # 按照浏览量排序
            queryset = queryset.order_by('-view')
        elif sort_by == 'add_time':
            # 按照时间排序
            queryset = queryset.order_by('-add_time')
        search = self.request.query_params.get('query')
        if search:
            data = NewsSearch.filter_msg(search, "news")
            ids = [d['_id'].replace('-', '') for d in data['hits']['hits']]
            queryset = queryset.filter(id__in=ids)
        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return NewsRetrieveSerializer
        else:
            return NewsSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.view += 1
        instance.save()
        serializer = self.get_serializer(instance)
        res = serializer.data
        return Response(res)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        news = News.objects.filter(id=serializer.data['id'])
        url = settings.HOST + 'news/' + str(serializer.data['id'])
        news.update(url=url)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        NewsSearch.import_index()

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

    def get_queryset(self):
        queryset = self.queryset.all()
        show = self.request.query_params.get('is_published')
        if show:
            queryset.filter(is_published=True)

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
