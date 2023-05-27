from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from backend.utils.permissions import IsOwner, IsAdminOrReadOnly
from rest_framework.response import Response
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from user.models import Message
from django.conf import settings
from article.models import Article, Category, Tag, Like, LikeDetail, Comment, Discussion
from article.serializer import ArticleCreateSerializer, CategorySerializer, TagSerializer, ArticleSerializer,\
    CommentSerializer, DiscussionSerializer, DiscussionCreateSerializer
import uuid
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from rest_framework import viewsets
from rest_framework.views import APIView
import oss2
from django.contrib.contenttypes.models import ContentType
from article.filter import ArticleFilterBackend
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from rest_framework import status, mixins

es = Elasticsearch(["http://127.0.0.1:9200"])


class ArticleSearch:
    @staticmethod
    def import_index():
        query_obj = Article.objects.all()
        action = [
            {
                "_index": "article",
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


class ESArticle(APIView):
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
        es.indices.create(index="article", body=body)
        print("索引创建成功")
        return Response('ok')


class ArticleView(viewsets.ModelViewSet):
    permission_classes = [IsOwner]
    filter_backends = (DjangoFilterBackend, SearchFilter, ArticleFilterBackend)
    search_fields = ['title', 'author__name', 'desc']
    queryset = Article.objects.all()

    def get_queryset(self):
        queryset = self.queryset.all()
        # 获取请求参数中的排序字段
        sort_by = self.request.query_params.get('ordering')
        # es.indices.close(index='article')
        if sort_by == 'synthesis':
            # 综合排序，按照浏览量和时间进行排序
            queryset = queryset.order_by('-view', '-add_time')
        elif sort_by == 'view':
            # 按照浏览量排序
            queryset = queryset.order_by('-view')
        elif sort_by == 'add_time':
            # 按照时间排序
            queryset = queryset.order_by('-add_time')
        search = self.request.query_params.get('query')
        if search:
            data = ArticleSearch.filter_msg(search, "article")
            ids = [d['_id'].replace('-', '') for d in data['hits']['hits']]
            queryset = queryset.filter(id__in=ids)
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return ArticleCreateSerializer
        else:
            return ArticleSerializer

    def perform_create(self, serializer):
        # 写url
        serializer.save(author=self.request.user)
        ArticleSearch.import_index()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.view += 1
        instance.save()
        serializer = self.get_serializer(instance)
        res = serializer.data
        return Response(res)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_200_OK)


class CategoryView(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = [IsAdminOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_200_OK)


class TagView(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = [IsAdminOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_200_OK)


class LikeView(APIView):

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        """
        获取点赞数
        :param
        type: 类型 article
        id: id
        :return:
        """
        data = {}
        try:
            # 获取对象模型
            type = request.GET.get('type')
            id = request.GET.get('id')
            c = ContentType.objects.get(model=type)
            # 根据模型和id获取likes对象
            l = Like.objects.get(object_type=c, object_id=id)
            # 获取数量
            data['count'] = l.count
            if request.user and LikeDetail.objects.filter(likes=l, user=request.user).exists():
                res = LikeDetail.objects.filter(likes=l, user=request.user).first()
                data['active'] = res.is_like
            else:
                data['active'] = False
        except Exception as e:
            print(e)
            data['count'] = 0
        return Response(data=data)

    def post(self, request):
        """
        点赞
        :param type: 类型 article
        id: id
        direct: 点赞
        :return:
        """
        data = {}
        type = request.data.get('type')
        id = request.data.get('id')
        user = request.user
        if not user:
            return Response(data={'code': -1, 'message': '未登录'}, status=status.HTTP_403_FORBIDDEN)
        star = 1 if int(request.data.get('star')) == 1 else -1
        c = ContentType.objects.get(model=type)
        # 点赞
        try:
            model = Like.objects.get(object_type=c, object_id=id)
        except Exception as e:
            model = Like(object_type=c, object_id=id)
        # 点赞
        model.save()
        clone_model = c.model_class().objects.get(id=id)
        if star == 1:
            detail = LikeDetail(likes=model, user=user)
            detail.save()
            if type == 'article':
                msg = Message(user=clone_model.author, to_user=user,
                              message='赞了你的文章'.format(user.username), type='like', object_type=c, object_id=id)
            if type == 'discussion':
                msg = Message(user=clone_model.author,to_user=user,
                              message='赞了你的动态', type='like', object_type=c, object_id=id)
            if type == 'comment':
                Comment.objects
                msg = Message(user=clone_model.user, to_user=user,
                              message='赞了你的评论'.format(user.username), type='like', object_type=c, object_id=id)
            msg.save()
        elif star == -1:
            LikeDetail.objects.get(likes=model, user=user).delete()
        clone_model.like += star
        if clone_model.like < 0:
            clone_model.like = 0
        clone_model.save()
        data['status'] = True if int(request.data.get('star')) == 1 else False
        return Response(data=data)


class UserComment(mixins.ListModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    queryset = Comment.objects.all().order_by('-created')
    permission_classes = [AllowAny]
    serializer_class = CommentSerializer

    def get_queryset(self):
        if self.action != 'destroy':
            type = self.request.query_params.get('type')
            parent = self.request.query_params.get('parent')
            id = self.request.query_params.get('object_id').replace('-', '')
            c = ContentType.objects.get(model=type)
            queryset = Comment.objects.filter(object_type=c, object_id=id, parent_id=parent)
        else:
            queryset = self.queryset
        return queryset

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        type = request.data.get('type')
        c = ContentType.objects.get(model=type)
        object_id = request.data.get('object_id').replace('-', '')
        clone_model = c.model_class().objects.get(id=object_id)
        clone_model.comment -= 1
        clone_model.save()
        parent_comment = Comment.objects.get(id=instance.parent_id)
        parent_comment.comment -= 1
        parent_comment.save()
        Message.objects.filter(link_id=instance.id).delete()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_200_OK, data={'count': clone_model.comment})


class CommentView(APIView):

    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request):
        try:
            user = request.user
            if not user:
                return Response(data={'code': -1, 'message': '未登录'}, status=status.HTTP_403_FORBIDDEN)
            content = request.data.get('content')
            image = request.data.get('image')
            object_id = request.data.get('object_id').replace('-', '')
            parent_comment_id = request.data.get('parent_comment_id')
            type = request.data.get('type')
            c = ContentType.objects.get(model=type)
            new_comment = Comment(content=content, user=user, image=image, object_type=c, object_id=object_id)
            if parent_comment_id:
                parent_comment = Comment.objects.get(id=parent_comment_id)
                parent_id = parent_comment.get_root().id
                new_comment.parent_id = parent_id
                parent_comment_parent = Comment.objects.get(id=parent_id)
                parent_comment_parent.comment += 1
                parent_comment_parent.save()
                new_comment.reply_to = parent_comment.user
                new_comment.save()
                msg = Message(user=parent_comment.user, to_user=user,
                              message='{}回复了你'.format(user.username),
                              type='comment',
                              object_type=ContentType.objects.get(model='comment'),
                              object_id=parent_comment.id,
                              link_id=new_comment.id)
                msg.save()
            else:
                new_comment.save()
                if type == 'article':
                    msg = Message(user=Article.objects.get(id=object_id).author,
                                  to_user=user,
                                  message='{}评论了你的文章'.format(user.username),
                                  type='comment', object_type=c,
                                  object_id=object_id, link_id=new_comment.id)
                    msg.save()
                elif type == 'discussion':
                    msg = Message(user=Discussion.objects.get(id=object_id).author,
                                  to_user=user,
                                  message='{}评论了你的动态'.format(user.username),
                                  type='comment',
                                  object_type=c,
                                  object_id=object_id, link_id=new_comment.id)
                    msg.save()
            clone_model = c.model_class().objects.get(id=object_id)
            clone_model.comment += 1
            clone_model.save()
            count = Comment.objects.filter(object_id=object_id).count()
            return Response(data={'count': count})
        except Exception as e:
            print(e)
            return Response(data={'code': -1, 'message': e}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


AccessKeyId = settings.ACCESS_KEYID
AccessKeySecret = settings.ACCESS_KEY_SECRET
auth = oss2.Auth(AccessKeyId, AccessKeySecret)
bucket = oss2.Bucket(auth, 'http://oss-cn-beijing.aliyuncs.com', 'lab-community')
bucket.create_bucket(oss2.models.BUCKET_ACL_PUBLIC_READ)
base_file_url = settings.FILE_URL


def update_fil_file(file):
    """
    ！ 上传单张图片
    :param file: b字节文件
    :return: 若成功返回图片路径，若不成功返回空
    """
    number = uuid.uuid4()
    base_fil_name = str(number) + '.jpg'
    file_name = base_file_url + base_fil_name
    res = bucket.put_object(base_fil_name, file)
    if res.status == 200:
        return file_name
    else:
        return False


class UploadImageAPIView(APIView):

    def post(self, request):
        file = request.FILES.get('file').read()
        file_url = update_fil_file(file)
        return Response(data=file_url)


class DiscussionView(viewsets.ModelViewSet):
    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = [IsOwner]

    def perform_create(self, serializer):
        # 写url
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return DiscussionCreateSerializer
        else:
            return DiscussionSerializer

    def get_queryset(self):
        queryset = Discussion.objects.all()
        sort_by = self.request.query_params.get('ordering')
        if sort_by == 'like':
            # 按照浏览量排序
            queryset = queryset.order_by('-like').order_by('-comment').order_by('-add_time')
        elif sort_by == 'time':
            # 按照时间排序
            queryset = queryset.order_by('-add_time')
        return queryset

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_200_OK)
