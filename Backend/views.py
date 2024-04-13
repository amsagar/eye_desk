import datetime

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import AllowAny

from .models import AdminModel, ClientModel, ScreenshotModel, DailyActivity, WeeklyActivity
from .serializers import AdminModelSerializer, ClientModelSerializer, ResponseDailyActivitySerializer, \
    WeeklyActivitySerializer, ResponseClientSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.utils.dateparse import parse_date


@swagger_auto_schema(
    method='post',
    request_body=AdminModelSerializer,
    responses={
        status.HTTP_201_CREATED: AdminModelSerializer(),
        status.HTTP_400_BAD_REQUEST: "Invalid request data"
    }
)
@csrf_exempt
@api_view(['POST'])
def signup(request):
    serializer = AdminModelSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['emailId', 'password'],
        properties={
            'emailId': openapi.Schema(type=openapi.TYPE_STRING),
            'password': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ),
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'emailId': openapi.Schema(type=openapi.TYPE_STRING),
            }
        ),
        404: "Invalid email or password"
    }
)
@csrf_exempt
@api_view(['POST'])
def signin(request):
    email = request.data.get('emailId')
    password = request.data.get('password')
    try:
        admin = AdminModel.objects.get(emailId=email, password=password)
        serializer = AdminModelSerializer(admin)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except AdminModel.DoesNotExist:
        return Response({"error": "Invalid email or password"}, status=status.HTTP_404_NOT_FOUND)


@swagger_auto_schema(
    method='post',
    request_body=ClientModelSerializer,
    responses={
        status.HTTP_201_CREATED: ClientModelSerializer(),
        status.HTTP_400_BAD_REQUEST: "Invalid Input"
    }
)
@csrf_exempt
@api_view(['POST'])
def createclient(request):
    serializer = ClientModelSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['emailId', 'password'],
        properties={
            'emailId': openapi.Schema(type=openapi.TYPE_STRING),
            'password': openapi.Schema(type=openapi.TYPE_STRING)
        },
    ),
    responses={
        200: ClientModelSerializer,
        404: openapi.Response(
            description="Invalid email or password",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": openapi.Schema(type=openapi.TYPE_STRING)
                }
            )
        )
    }
)
@csrf_exempt
@api_view(['POST'])
def login(request):
    email = request.data.get('emailId')
    password = request.data.get('password')
    try:
        client = ClientModel.objects.get(emailId=email, password=password)
        serializer = ClientModelSerializer(client)
        return Response(serializer.data)
    except ClientModel.DoesNotExist:
        return Response({"error": "Invalid email or password"}, status=status.HTTP_404_NOT_FOUND)


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('date', openapi.IN_QUERY, description="Date in  YYYY-MM-DD format.",
                          type=openapi.TYPE_STRING),
        openapi.Parameter('client_id', openapi.IN_QUERY, description="ID of the client", type=openapi.TYPE_INTEGER),
    ],
    responses={
        200: openapi.Response(description='Success', schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'daily_activity': openapi.Schema(type=openapi.TYPE_NUMBER),
                'daily_hours': openapi.Schema(type=openapi.TYPE_NUMBER),
                'weekly_activity': openapi.Schema(type=openapi.TYPE_NUMBER),
                'weekly_activity_hours': openapi.Schema(type=openapi.TYPE_NUMBER),
                'week_earned': openapi.Schema(type=openapi.TYPE_NUMBER),
                'screenshots': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'url': openapi.Schema(type=openapi.TYPE_STRING),
                        'time': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
                    }
                )),
            }
        )),
        400: "Bad Request: If required parameters are missing or invalid."
    }
)
@csrf_exempt
@api_view(['GET'])
def get_screenshots(request):
    date = request.query_params.get('date')
    client_id = request.query_params.get('client_id')
    if not (date and client_id):
        return JsonResponse({'error': 'Both date and client_id are required parameters'},
                            status=status.HTTP_400_BAD_REQUEST)
    try:
        date = parse_date(date)
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=status.HTTP_400_BAD_REQUEST)
    if date is None:
        return JsonResponse({'error': 'Invalid date value'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        screenshots = ScreenshotModel.objects.filter(date=date, client_id=client_id)
    except ScreenshotModel.DoesNotExist:
        return JsonResponse({'error': 'No screenshots found for the given date and client_id'},
                            status=status.HTTP_404_NOT_FOUND)
    screenshots_map = {}
    for screenshot in screenshots:
        time_12hr_format = screenshot.time.strftime('%I:%M %p')
        screenshots_map[str(time_12hr_format)] = screenshot.url
    try:
        daily_activity = DailyActivity.objects.get(date=date, client_id=client_id)
    except DailyActivity.DoesNotExist:
        return JsonResponse({'error': 'No daily activity found for the given date and client_id'},
                            status=status.HTTP_404_NOT_FOUND)
    daily_serializer = ResponseDailyActivitySerializer(daily_activity)
    daily_data = daily_serializer.data
    try:
        weekly_activity = WeeklyActivity.objects.get(client_id=client_id)
    except WeeklyActivity.DoesNotExist:
        return JsonResponse({'error': 'No weekly activity found for the given client_id'},
                            status=status.HTTP_404_NOT_FOUND)
    weekly_serializer = WeeklyActivitySerializer(weekly_activity)
    weekly_data = weekly_serializer.data
    return Response({
        'dailyActivity': daily_data,
        'weeksActivity': weekly_data.get('weeksActivity', 0),
        'activityHours': weekly_data.get('activityHours', 0),
        'weekEarned': weekly_data.get('weekEarned', 0),
        'screenshots': screenshots_map
    }, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='get',
    responses={
        200: openapi.Response(description='Success', schema=openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'fullName': openapi.Schema(type=openapi.TYPE_STRING),
                    'emailId': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL),
                    'salary': openapi.Schema(type=openapi.TYPE_NUMBER),
                }
            )
        )),
        400: "Bad Request."
    }
)
@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def client_list(request):
    clients = ClientModel.objects.all()
    serializer = ResponseClientSerializer(clients, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('from_date', openapi.IN_QUERY, type=openapi.TYPE_STRING,
                          description='Start date (YYYY-MM-DD)', required=True),
        openapi.Parameter('to_date', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='End date (YYYY-MM-DD)',
                          required=True),
        openapi.Parameter('client_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='Client ID',
                          required=True)
    ],
    responses={
        200: 'Success',
        400: 'Bad Request',
        404: 'Not Found'
    },
    operation_description="Retrieve screenshots and activity data for a client within a date range."
)
@csrf_exempt
@api_view(['GET'])
def get_reports(request):
    from_date = request.query_params.get('from_date')
    to_date = request.query_params.get('to_date')
    client_id = request.query_params.get('client_id')

    if not (from_date and to_date and client_id):
        return JsonResponse({'error': 'from_date, to_date, and client_id are required parameters'},
                            status=status.HTTP_400_BAD_REQUEST)

    try:
        from_date = parse_date(from_date)
        to_date = parse_date(to_date)
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=status.HTTP_400_BAD_REQUEST)

    if from_date is None or to_date is None:
        return JsonResponse({'error': 'Invalid date value'}, status=status.HTTP_400_BAD_REQUEST)

    # Check if start and end dates match stored data
    stored_weekly_activity = WeeklyActivity.objects.filter(client_id=client_id, startDate=from_date,
                                                           endDate=to_date).first()
    if not stored_weekly_activity:
        return JsonResponse({'error': 'No weekly activity found for the given date range and client_id'},
                            status=status.HTTP_400_BAD_REQUEST)

    screenshots_data = []
    date_range = range((to_date - from_date).days + 1)

    for i in date_range:
        current_date = from_date + datetime.timedelta(days=i)

        try:
            screenshots = ScreenshotModel.objects.filter(date=current_date, client_id=client_id)
        except ScreenshotModel.DoesNotExist:
            screenshots = []

        screenshots_map = {}
        for screenshot in screenshots:
            time_12hr_format = screenshot.time.strftime('%I:%M %p')
            screenshots_map[str(time_12hr_format)] = screenshot.url

        try:
            daily_activity = DailyActivity.objects.get(date=current_date, client_id=client_id)
            daily_serializer = ResponseDailyActivitySerializer(daily_activity)
            daily_data = daily_serializer.data
        except DailyActivity.DoesNotExist:
            daily_data = {}

        screenshots_data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'dailyActivity': daily_data,
            'screenshots': screenshots_map
        })
    weekly_serializer = WeeklyActivitySerializer(stored_weekly_activity)
    weekly_data = weekly_serializer.data
    return JsonResponse({
        'screenshots_data': screenshots_data,
        'weeksActivity': weekly_data.get('weeksActivity', 0),
        'activityHours': weekly_data.get('activityHours', 0),
        'weekEarned': weekly_data.get('weekEarned', 0)
    }, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('from_date', openapi.IN_QUERY, type=openapi.TYPE_STRING,
                          description='Start date (YYYY-MM-DD)', required=True),
        openapi.Parameter('to_date', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='End date (YYYY-MM-DD)',
                          required=True),
        openapi.Parameter('client_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='Client ID',
                          required=True)
    ],
    responses={
        200: openapi.Response(description='Success', schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'screenshots_data': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE,
                                                   description='Date in YYYY-MM-DD format'),
                            'dailyActivity': openapi.Schema(type=openapi.TYPE_OBJECT,
                                                            description='Daily activity data'),
                            'screenshots': openapi.Schema(type=openapi.TYPE_OBJECT, description='Screenshots data')
                        }
                    )
                )
            }
        )),
        400: 'Bad Request'
    },
    operation_description="Retrieve screenshots and daily activity data for a client within a date range."
)
@csrf_exempt
@api_view(['GET'])
def get_daily_reports(request):
    from_date = request.query_params.get('from_date')
    to_date = request.query_params.get('to_date')
    client_id = request.query_params.get('client_id')

    if not (from_date and to_date and client_id):
        return JsonResponse({'error': 'from_date, to_date, and client_id are required parameters'},
                            status=status.HTTP_400_BAD_REQUEST)
    try:
        from_date = parse_date(from_date)
        to_date = parse_date(to_date)
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=status.HTTP_400_BAD_REQUEST)

    if from_date is None or to_date is None:
        return JsonResponse({'error': 'Invalid date value'}, status=status.HTTP_400_BAD_REQUEST)
    screenshots_data = []
    date_range = range((to_date - from_date).days + 1)
    for i in date_range:
        current_date = from_date + datetime.timedelta(days=i)
        try:
            screenshots = ScreenshotModel.objects.filter(date=current_date, client_id=client_id)
        except ScreenshotModel.DoesNotExist:
            screenshots = []

        screenshots_map = {}
        for screenshot in screenshots:
            time_12hr_format = screenshot.time.strftime('%I:%M %p')
            screenshots_map[str(time_12hr_format)] = screenshot.url

        try:
            daily_activity = DailyActivity.objects.get(date=current_date, client_id=client_id)
            daily_serializer = ResponseDailyActivitySerializer(daily_activity)
            daily_data = daily_serializer.data
        except DailyActivity.DoesNotExist:
            daily_data = {}

        screenshots_data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'dailyActivity': daily_data,
            'screenshots': screenshots_map
        })

    return JsonResponse({
        'screenshots_data': screenshots_data,
    }, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('date', openapi.IN_QUERY, type=openapi.TYPE_STRING,
                          description='Date (YYYY-MM-DD)', required=True),
        openapi.Parameter('client_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='Client ID',
                          required=True)
    ]
)
@api_view(['GET'])
@csrf_exempt
def get_daily_hours(request):
    date_str = request.query_params.get('date')
    cli_id = request.query_params.get('client_id')
    try:
        date = parse_date(date_str)
        daily_activity = get_object_or_404(DailyActivity, client_id=cli_id, date=date)
        daily_hours = daily_activity.dailyHours
        print(daily_hours)
        hours = int(daily_hours)
        minutes = int((daily_hours - hours) * 60)
        seconds = int(((daily_hours - hours) * 60 - minutes) * 60)
        daily_hours_formatted = "{:02}:{:02}:{:02}".format(hours, minutes, seconds)
        return JsonResponse({'dailyHours': daily_hours_formatted})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
