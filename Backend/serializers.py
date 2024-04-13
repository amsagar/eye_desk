from rest_framework import serializers
from .models import *


class AdminModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminModel
        fields = ['id', 'fullName', 'emailId', 'password']


class ClientModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientModel
        fields = ['id', 'fullName', 'emailId', 'password', 'salary']


class DailyActivitySerializer(serializers.ModelSerializer):
    client = serializers.PrimaryKeyRelatedField(queryset=ClientModel.objects.all())

    class Meta:
        model = DailyActivity
        fields = ['id', 'date', 'dailyActivity', 'dailyHours', 'client']


class ScreenshotModelSerializer(serializers.ModelSerializer):
    client = serializers.PrimaryKeyRelatedField(queryset=ClientModel.objects.all())

    class Meta:
        model = ScreenshotModel
        fields = ['id', 'client', 'activity', 'url', 'date', 'time']


class WeeklyActivitySerializer(serializers.ModelSerializer):
    client = serializers.PrimaryKeyRelatedField(queryset=ClientModel.objects.all())

    class Meta:
        model = WeeklyActivity
        fields = ['id', 'startDate', 'endDate', 'activityHours', 'weeksActivity', 'weekEarned', 'client']


class ResponseDailyActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyActivity
        fields = ('dailyActivity', 'dailyHours')


class ResponseWeeklyActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = WeeklyActivity
        fields = ('weeksActivity', 'activityHours', 'weekEarned')


class ResponseClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientModel
        fields = ['id', 'fullName', 'emailId', 'salary']


class ScreenshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScreenshotModel
        fields = ['client', 'url', 'date', 'time']
