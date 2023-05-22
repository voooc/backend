# -*- coding:utf-8 -*-
from rest_framework import serializers
from user.models import Message, Follows, User, Roles, Departments
from django.contrib.auth.hashers import make_password
from article.serializer import UserArticleSerializer, TagSerializer, CategorySerializer
from article.models import LikeDetail, Like, Article, Discussion, Comment
from django.contrib.contenttypes.models import ContentType


class UserCreateSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    department = serializers.CharField(source='department.name')
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        return attrs

    @staticmethod
    def get_roles(obj):
        return [{'name': role.name, 'value': role.value} for role in obj.roles.all()]

    def create(self, validated_data):
        validated_data['department_id'] = validated_data['department']['name']
        del validated_data['department']
        validated_data['password'] = make_password(validated_data['password'])
        user = super().create(validated_data)
        user.is_active = False
        role_id = Roles.objects.get(value='USER')
        user.roles.add(role_id)
        # 添加默认密码
        user.save()
        return user

    class Meta:
        model = User
        fields = ('id', 'username', 'image', 'email', 'password', 'desc',
                  'roles', 'department', 'name', 'is_active')
        extra_kwargs = {
            'password': {
                'write_only': True
            },
        }


class DepartmentsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Departments
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    department = DepartmentsSerializer(read_only=True)


    @staticmethod
    def get_roles(obj):
        return [{'name': role.name, 'value': role.value} for role in obj.roles.all()]

    class Meta:
        model = User
        fields = ('id', 'username', 'image', 'email', 'desc', 'roles', 'department', 'date_joined', 'name', 'is_active')


class RolesSerializer(serializers.ModelSerializer):
    create_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)

    class Meta:
        model = Roles
        fields = '__all__'


class MessageSerializer(serializers.ModelSerializer):
    add_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    to_user = UserSerializer(read_only=True)
    user = UserSerializer(read_only=True)

    def to_representation(self, instance):
        res = super(MessageSerializer, self).to_representation(instance=instance)
        user_interface = {
            'is_follow': False,
        }
        dst_info = {
            'image': '',
            'title': '',
            'detail': '',
            'id_type': '',
        }
        parent_info = {
            'id_type': '',
            'detail': '',
            'item_id': '',
        }
        if instance.type == 'follow':
            follow_active = Follows.objects.filter(fan=instance.user.id, follow_id=instance.to_user.id).exists()
            user_interface['is_follow'] = follow_active
        res.setdefault('user_interface', user_interface)
        if instance.type == 'like' or instance.type == 'comment':
            article = ContentType.objects.get(model='article')
            comment = ContentType.objects.get(model='comment')
            discussion = ContentType.objects.get(model='discussion')
            if article.id == instance.object_type.id:
                dst_info['id_type'] = 'article'
                model = Article.objects.get(id=instance.object_id)
                dst_info['image'] = model.avatar
                dst_info['title'] = model.title
            elif discussion.id == instance.object_type.id:
                dst_info['id_type'] = 'discussion'
                model = Discussion.objects.get(id=instance.object_id)
                dst_info['detail'] = model.content
            elif comment.id == instance.object_type.id:
                dst_info['id_type'] = 'comment'
                model = Comment.objects.get(id=instance.object_id)
                dst_info['detail'] = model.content
                if model.object_type.id == article.id:
                    parent_info['id_type'] = 'article'
                    temp = Article.objects.get(id=model.object_id)
                    parent_info['item_id'] = temp.id
                    parent_info['detail'] = temp.title
                elif model.object_type.id == discussion.id:
                    parent_info['id_type'] = 'discussion'
                    temp = Discussion.objects.get(id=model.object_id)
                    parent_info['item_id'] = temp.id
                    parent_info['detail'] = temp.content
        if instance.type == 'comment':
            model = Comment.objects.get(id=instance.link_id)
            dst_info['detail'] = model.content
        res.setdefault('dst_info', dst_info)
        res.setdefault('parent_info', parent_info)
        return res

    class Meta:
        model = Message
        fields = '__all__'


class FollowCreateSerializer(serializers.ModelSerializer):
    follow = serializers.CharField(source='user.id')
    type = serializers.CharField()

    class Meta:
        model = Follows
        fields = ('follow', 'type', )


class FollowSerializer(serializers.ModelSerializer):
    follow = UserArticleSerializer(read_only=True)
    fan = UserArticleSerializer(read_only=True)

    def to_representation(self, instance):
        res = super(FollowSerializer, self).to_representation(instance=instance)
        user = self.context['request'].user
        fan = self.context['request'].query_params.get('fan')
        follow = self.context['request'].query_params.get('follow')
        user_interface = {
            'is_follow': False,
        }
        if not user.is_anonymous:
            if fan:
                is_active = Follows.objects.filter(fan=user,
                                                   follow=res.get('fan')['id']).exists()
                access = is_active
                user_interface['is_follow'] = access
            elif follow:
                is_active = Follows.objects.filter(fan=user,
                                                   follow=res.get('follow')['id']).exists()
                access = is_active
                user_interface['is_follow'] = access
        else:
            user_interface['is_follow'] = False
        res.setdefault('user_interface', user_interface)
        return res

    class Meta:
        model = Follows
        fields = '__all__'


class LikeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Like
        fields = '__all__'


class LikeArticleSerializer(serializers.ModelSerializer):
    author = UserArticleSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    add_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)

    class Meta:
        model = Article
        fields = '__all__'


class LikeDetailSerializer(serializers.ModelSerializer):
    likes = LikeSerializer(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = LikeDetail
        fields = '__all__'
