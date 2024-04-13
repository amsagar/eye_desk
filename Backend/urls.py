from django.urls import path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from . import views

schema_view = get_schema_view(
    openapi.Info(
        title="Eye Desk",
        default_version='v1',
        description="Backend API's",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="sinchana@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('createclient/', views.createclient, name='createclient'),
    path('login/', views.login, name='login'),
    path('startactivity/', views.start_activity, name='start_activity'),
    path('stopactivity/', views.stop_activity, name='stop_activity'),
    path('getScreenshots/', views.get_screenshots, name='get_screenshots'),
    path('getClients/', views.client_list, name='get_clients'),
    path('getWeeklyReports/', views.get_reports, name='get_weekly_reports'),
    path('getDailyReports/', views.get_daily_reports, name='get_daily_reports'),
    path('', views.hello_world, name='hello_world')
]
