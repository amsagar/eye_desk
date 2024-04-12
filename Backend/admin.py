from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(ClientModel)
admin.site.register(AdminModel)
admin.site.register(WeeklyActivity)
admin.site.register(DailyActivity)
admin.site.register(ScreenshotModel)
