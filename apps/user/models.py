from datetime import datetime
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=60, blank=True, null=True, verbose_name='姓名')
    desc = models.CharField(max_length=100, verbose_name='个人介绍', default='码农', null=True, blank=True)
    image = models.URLField(default='https://lab-community.oss-cn-beijing.aliyuncs.com/default.jpg', blank=True, verbose_name = '头像')
    email = models.EmailField(unique=True, default='')
    sex = models.IntegerField(choices=(
        (0, '女性'),
        (1, '男性'),
    ), default=1)
    roles = models.ManyToManyField('user.Roles', blank=True,
                                   verbose_name='角色')
    department = models.ForeignKey('user.Departments', null=True, blank=True, on_delete=models.SET_NULL,
                                   verbose_name='部门')

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username

    def get_roles_values(self):
        return [role[0] for role in list(self.roles.values_list('value'))]

    def get_user_info(self):
        roles = [role[0] for role in list(self.roles.values_list('name'))]
        # 获取用户信息
        user_info = {
            'id': self.pk,
            'username': self.username,
            'name': self.name,
            'desc': self.desc,
            'sex': self.sex,
            'image': str(self.image),
            'department': self.department.id,
            'roles': roles if len(roles) else [],
            'email': self.email,
            'is_active': self.is_active,
        }
        return user_info


class Roles(models.Model):
    """
    角色
    """
    name = models.CharField(max_length=32, verbose_name='角色')
    value = models.CharField(max_length=32, verbose_name='角色值', unique=True)
    desc = models.CharField(max_length=50, blank=True, default='', verbose_name='描述')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '角色'
        verbose_name_plural = verbose_name
        ordering = ['id']


class Departments(models.Model):
    """
    组织架构 部门
    """
    name = models.CharField(max_length=32, unique=True, verbose_name='部门')
    add_time = models.DateTimeField(verbose_name='添加时间', default=datetime.now)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '部门'
        verbose_name_plural = verbose_name
        ordering = ['id']


class Follows(models.Model):
    """关注表"""
    follow = models.ForeignKey(User, on_delete=models.CASCADE, related_name='follow', verbose_name='被关注者')
    fan = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fan', verbose_name='粉丝')
    add_time = models.DateTimeField(auto_now_add=True, verbose_name='添加时间')

    def __str__(self):
        return str(self.follow.id)

    class Meta:
        ordering = ('-follow',)


class VerifyCode(models.Model):
    """邮箱验证码"""
    code = models.CharField(verbose_name='验证码', max_length=10)
    email = models.EmailField(verbose_name='邮箱', default='')
    send_choices = (
        ('register', '注册'),
        ('forget', '找回密码'),
        ('update_email', '修改邮箱')
    )
    send_type = models.CharField(verbose_name='验证码类型', max_length=30, choices=send_choices, default='register')

    send_time = models.DateTimeField(default=datetime.now, verbose_name='发送时间')

    def __str__(self):
        return self.code

    class Meta:
        verbose_name = '邮箱验证码'
        verbose_name_plural = verbose_name


class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user', verbose_name='收消息用户')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='to_user', verbose_name='发消息用户', blank=True, null=True)
    message = models.TextField(verbose_name='消息内容')
    type = models.CharField(default='system', verbose_name='信息类型', max_length=100, blank=True)
    has_read = models.BooleanField(default=False, verbose_name='是否已读')
    add_time = models.DateTimeField(default=datetime.now, verbose_name='添加时间')
    object_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.CharField(max_length=128, null=True, blank=True)
    content_object = GenericForeignKey(
        ct_field="object_type",
        fk_field="object_id"
    )
    link_id = models.CharField(max_length=128, null=True, blank=True, verbose_name='相关联信息id')

    def __str__(self):
        return self.message

    class Meta:
        verbose_name = '用户消息'
        verbose_name_plural = verbose_name
        ordering = ('-add_time',)
