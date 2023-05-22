from rest_framework import serializers
from news.models import News, Banner, Announcement, Awards


class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = '__all__'


class NewsRetrieveSerializer(serializers.ModelSerializer):
    previous = serializers.CharField(read_only=True)
    next = serializers.CharField(read_only=True)

    class Meta:
        model = News
        fields = '__all__'


class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = '__all__'


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = '__all__'


class AwardsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Awards
        fields = '__all__'