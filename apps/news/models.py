from django.db import models


class News(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    add_time = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=True)
    image = models.URLField(max_length=200, blank=True)
    desc = models.CharField(max_length=256, blank=True, null=True)
    url = models.CharField(max_length=200, blank=True, null=True)
    view = models.PositiveIntegerField(default=0, verbose_name='阅读数量')

    class Meta:
        ordering = ('-add_time',)


class Announcement(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    add_time = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ('-add_time',)


class Banner(models.Model):
    image = models.URLField(max_length=200, blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    add_time = models.DateTimeField(auto_now_add=True)
    order = models.CharField(max_length=255, default=999)
    link = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        ordering = ['-order']


class Awards(models.Model):
    image = models.URLField(max_length=200, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    people = models.CharField(max_length=255, blank=True, null=True)
    add_time = models.DateTimeField(null=True)

    class Meta:
        ordering = ['-add_time']