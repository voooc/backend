import uuid
from datetime import datetime
from django.db import models
from user.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from mptt.models import MPTTModel, TreeForeignKey


class Category(models.Model):
    name = models.CharField(max_length=100)
    add_time = models.DateTimeField(default=datetime.now)

    class Meta:
        verbose_name = '分类'
        verbose_name_plural = verbose_name


class Tag(models.Model):
    name = models.CharField(max_length=100)
    add_time = models.DateTimeField(default=datetime.now)

    class Meta:
        verbose_name = '标签'
        verbose_name_plural = verbose_name


class Article(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, verbose_name='分类', null=True, blank=True)
    title = models.CharField(max_length=100, default='无标题')
    code_highlight = models.CharField(max_length=50, verbose_name='代码高亮模式', default='atom')
    preview = models.CharField(max_length=50, verbose_name='markdown模式', default='default')
    tags = models.ManyToManyField('article.Tag', verbose_name='标签')
    desc = models.CharField(max_length=256, blank=True, null=True)
    avatar = models.URLField(max_length=200, blank=True, null=True)
    url = models.URLField(max_length=200, blank=True, null=True)
    # utf8mb4_0900_ai_ci
    content = models.TextField()
    add_time = models.DateTimeField(auto_now_add=True)
    view = models.PositiveIntegerField(default=0, verbose_name='阅读数量')
    like = models.PositiveIntegerField(default=0, verbose_name='点赞量')
    comment = models.PositiveIntegerField(default=0, verbose_name='评论量')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = '文章'
        verbose_name_plural = verbose_name
        ordering = ('-add_time',)


class Discussion(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    image = models.TextField(null=True, blank=True)
    # utf8mb4_0900_ai_ci
    content = models.TextField()
    like = models.PositiveIntegerField(default=0, verbose_name='点赞量')
    comment = models.PositiveIntegerField(default=0, verbose_name='评论量')
    add_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.id

    class Meta:
        verbose_name = '讨论'
        verbose_name_plural = verbose_name
        ordering = ('-add_time',)


class Like(models.Model):
    object_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=128)
    content_object = GenericForeignKey(
        ct_field="object_type",
        fk_field="object_id"
    )
    count = models.IntegerField(default=0)


class LikeDetail(models.Model):
    likes = models.ForeignKey(Like, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-date', )


class Comment(MPTTModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    image = models.TextField(null=True, blank=True)
    object_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.CharField(max_length=128, null=True, blank=True)
    content_object = GenericForeignKey(
        ct_field="object_type",
        fk_field="object_id"
    )
    content = models.TextField()
    like = models.PositiveIntegerField(default=0, verbose_name='点赞量')
    comment = models.PositiveIntegerField(default=0, verbose_name='评论量')
    created = models.DateTimeField(auto_now_add=True)
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )

    # 新增，记录二级评论回复给谁, str
    reply_to = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='reply_to'
    )

    def __str__(self):
        return self.content[:20]

    class MPTTMeta:
        order_insertion_by = ['created']
