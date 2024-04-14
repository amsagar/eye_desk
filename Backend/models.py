from django.db import models
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta


class AdminModel(models.Model):
    fullName = models.CharField(max_length=255)
    emailId = models.EmailField(unique=True)
    password = models.CharField(max_length=255)


class ClientModel(models.Model):
    fullName = models.CharField(max_length=255)
    emailId = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    salary = models.FloatField(max_length=255)


class ScreenshotModel(models.Model):
    client = models.ForeignKey(ClientModel, on_delete=models.CASCADE)
    url = models.URLField(max_length=1000)
    date = models.DateField()
    time = models.TimeField()


class DailyActivity(models.Model):
    date = models.DateField()
    dailyActivity = models.FloatField()
    dailyHours = models.DurationField()
    client = models.ForeignKey('ClientModel', on_delete=models.CASCADE)

    @classmethod
    def create_or_update(cls, date, daily_activity, daily_hours, client):
        existing_activity = cls.objects.filter(date=date, client=client).first()
        if existing_activity:
            existing_activity.dailyActivity = (existing_activity.dailyActivity + daily_activity) / 2
            existing_activity.dailyHours = daily_hours
            existing_activity.save()
        else:
            cls.objects.create(date=date, dailyActivity=daily_activity, dailyHours=daily_hours, client=client)


class WeeklyActivity(models.Model):
    startDate = models.DateField()
    endDate = models.DateField()
    activityHours = models.FloatField(default=0.0)  # Change to FloatField
    weeksActivity = models.FloatField(default=0.0)
    weekEarned = models.FloatField(default=0.0)
    client = models.ForeignKey('ClientModel', on_delete=models.CASCADE)

    @classmethod
    def calculate_weekly_activity(cls, client):
        today = timezone.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        weekly_activities = DailyActivity.objects.filter(date__gte=start_of_week, date__lte=end_of_week, client=client)
        total_activity_hours = 0.0  # Initialize total hours as float
        for activity in weekly_activities:
            total_activity_hours += activity.dailyHours.total_seconds() / 3600
        average_activity = weekly_activities.aggregate(Sum('dailyActivity'))[
                               'dailyActivity__sum'] / weekly_activities.count()
        salary_per_week = client.salary / 4
        if total_activity_hours >= 40:
            week_earned = salary_per_week  # If 40 or more hours are worked, full weekly salary is earned
        else:
            week_earned = (total_activity_hours / 40) * salary_per_week
        weekly_activity, created = cls.objects.get_or_create(startDate=start_of_week, endDate=end_of_week,
                                                             client=client)
        weekly_activity.activityHours = total_activity_hours
        weekly_activity.weeksActivity = average_activity
        weekly_activity.weekEarned = week_earned
        weekly_activity.save()
