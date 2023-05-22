#!/usr/bin/python
# -*- coding:utf-8 -*-
from rest_framework import serializers
from article.models import Article, Category, Tag, Comment, LikeDetail, Discussion
from user.models import User, Follows
from django.contrib.contenttypes.models import ContentType
from article.models import Like


class UserArticleSerializer(serializers.ModelSerializer):
    department = serializers.CharField(source='department.name')

    class Meta:
        model = User
        fields = ('email', 'id', 'image', 'username', 'desc', 'name', 'department')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class ArticleSerializer(serializers.ModelSerializer):
    author = UserArticleSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    add_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)

    def to_representation(self, instance):
        res = super(ArticleSerializer, self).to_representation(instance=instance)
        c = ContentType.objects.get(model='article')
        user = self.context["request"].user
        user_interface = {
            'is_like': False,
            'is_follow': False,
        }
        like = Like.objects.filter(object_type=c, object_id=instance.id)
        if like.exists():
            if not user.is_anonymous and LikeDetail.objects.filter(likes=like.first(), user=user).exists():
                follow_active = Follows.objects.filter(fan=user, follow_id=instance.author.id).exists()
                user_interface['is_follow'] = follow_active
                user_interface['is_like'] = True
            else:
                user_interface['is_like'] = False
        else:
            user_interface['is_like'] = False
        res.setdefault('user_interface', user_interface)
        return res

    class Meta:
        model = Article
        fields = '__all__'


class ArticleCreateSerializer(serializers.ModelSerializer):
    category_id = serializers.CharField(max_length=256)
    author = UserArticleSerializer(read_only=True)
    tags = TagSerializer(read_only=True, many=True)
    tags_id = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), write_only=True, many=True)

    def create(self, validated_data):
        tags_id_data = validated_data.pop('tags_id')
        article = Article.objects.create(**validated_data)
        article.url = article.url+'/#/article/'+str(article.id)
        for tags_data in tags_id_data:
            article.tags.add(tags_data)
        article.save()
        return article

    class Meta:
        model = Article
        fields = ('id', 'category_id', 'tags_id', 'tags', 'title', 'desc', 'avatar', 'content', 'view',
                  'author', 'code_highlight', 'preview', 'url')


class StringToArrayField(serializers.Field):
    def to_representation(self, value):
        # 将字符串转换为数组
        if value:
            return value.split(';')
        else:
            return []


class CommentSerializer(serializers.Serializer):
    user = UserArticleSerializer()
    id = serializers.CharField()
    image = StringToArrayField()
    created = serializers.DateTimeField()
    content = serializers.CharField()
    reply_to = UserArticleSerializer()
    like = serializers.IntegerField()
    comment = serializers.IntegerField()

    def to_representation(self, instance):
        res = super(CommentSerializer, self).to_representation(instance=instance)
        c = ContentType.objects.get(model='comment')
        user = self.context["request"].user
        user_interface = {
            'is_like': False,
        }
        like = Like.objects.filter(object_type=c, object_id=instance.id)
        if like.exists():
            if not user.is_anonymous and LikeDetail.objects.filter(likes=like.first(), user=user).exists():
                user_interface['is_like'] = True
            else:
                user_interface['is_like'] = False
        else:
            user_interface['is_like'] = False
        res.setdefault('user_interface', user_interface)
        return res

    class Meta:
        model = Comment
        fields = '__all__'


class DiscussionSerializer(serializers.ModelSerializer):
    author = UserArticleSerializer(read_only=True)
    image = StringToArrayField()

    def to_representation(self, instance):
        res = super(DiscussionSerializer, self).to_representation(instance=instance)
        c = ContentType.objects.get(model='discussion')
        user = self.context["request"].user
        user_interface = {
            'is_like': False,
        }
        like = Like.objects.filter(object_type=c, object_id=instance.id)
        if like.exists():
            if not user.is_anonymous and LikeDetail.objects.filter(likes=like.first(), user=user).exists():
                user_interface['is_like'] = True
            else:
                user_interface['is_like'] = False
        else:
            user_interface['is_like'] = False
        res.setdefault('user_interface', user_interface)
        return res

    class Meta:
        model = Discussion
        fields = '__all__'


class DiscussionCreateSerializer(serializers.ModelSerializer):
    author = UserArticleSerializer(read_only=True)

    class Meta:
        model = Discussion
        fields = '__all__'