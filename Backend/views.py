import datetime

from django.http import JsonResponse
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from .models import AdminModel, ClientModel, ScreenshotModel, DailyActivity, WeeklyActivity
from .serializers import AdminModelSerializer, ClientModelSerializer, ResponseDailyActivitySerializer, \
    WeeklyActivitySerializer, ClientSerializer
import threading
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from io import BytesIO
from PIL import ImageGrab
import time
import firebase_admin
from firebase_admin import credentials, storage
from django.utils import timezone
from django.utils.dateparse import parse_date

running = False
if not firebase_admin._apps:
    cred = credentials.Certificate("eyedesk-43706-firebase-adminsdk-qo8r1-6f48d8812a.json")
    firebase_admin.initialize_app(cred, {'storageBucket': 'eyedesk-43706.appspot.com'})
bucket = storage.bucket()
client_id = None
timer = None


def capture_screenshots():
    global running
    # interval = 10 * 60  # 10 minutes
    interval = 10
    while running:
        try:
            screenshot = ImageGrab.grab()
            screenshot_bytes = BytesIO()
            screenshot.save(screenshot_bytes, format='PNG')
            screenshot_bytes.seek(0)
            destination_blob_name = str(client_id) + "/screenshot_{0}.png".format(time.time())
            blob = bucket.blob(destination_blob_name)
            blob.upload_from_file(screenshot_bytes, content_type='image/png')
            # Set expiration time to a very large value (e.g., 10 years from now)
            expiration = datetime.datetime.now() + datetime.timedelta(days=365 * 100)
            url = blob.generate_signed_url(expiration=expiration, version='v2')
            print("File uploaded successfully. URL:", url)
            screenshot_data = {
                'client_id': client_id,
                'url': url,
                'date': timezone.now().date(),
                'time': timezone.now().time()
            }
            ScreenshotModel.objects.create(**screenshot_data)
            time.sleep(interval)
        except KeyboardInterrupt:
            break


@swagger_auto_schema(
    method='post',
    request_body=AdminModelSerializer,
    responses={
        status.HTTP_201_CREATED: AdminModelSerializer(),
        status.HTTP_400_BAD_REQUEST: "Invalid request data"
    }
)
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
@api_view(['POST'])
def signin(request):
    email = request.data.get('emailId')
    password = request.data.get('password')
    try:
        admin = AdminModel.objects.get(emailId=email, password=password)
        serializer = AdminModelSerializer(admin)
        return Response(serializer.data)
    except AdminModel.DoesNotExist:
        return Response({"error": "Invalid email or password"}, status=status.HTTP_404_NOT_FOUND)


@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'name': openapi.Schema(type=openapi.TYPE_STRING),
            'age': openapi.Schema(type=openapi.TYPE_INTEGER),
        }
    ),
    responses={
        status.HTTP_201_CREATED: ClientModelSerializer(),
        status.HTTP_400_BAD_REQUEST: "Invalid Input"
    }
)
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


@swagger_auto_schema(method='post', request_body=openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the Client'),
    }
))
@api_view(['POST'])
def start_activity(request):
    global running, client_id, timer
    if not running:
        client_id = request.data.get('id')
        try:
            ClientModel.objects.get(pk=client_id)
            running = True
            timer = datetime.datetime.now()
            screenshots_thread = threading.Thread(target=capture_screenshots)
            screenshots_thread.start()
            return Response({'message': 'Screenshot capturing started'}, status=status.HTTP_200_OK)
        except:
            return Response({'message': 'Client Id Does not exist'},
                            status=status.HTTP_404_NOT_FOUND)
    else:
        return Response({'message': 'Screenshot capturing is already in progress'}, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['client_id', 'focus_percentage'],
        properties={
            'client_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the Client'),
            'focus_percentage': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_DOUBLE)
        },
    ),
    responses={
        200: openapi.Response(description='Screenshot capturing stopped'),
        400: "Bad Request: If the screenshot capturing is not in progress or if required parameters are missing."
    }
)
@api_view(['POST'])
def stop_activity(request):
    global running, timer
    if request.method == 'POST':
        request_data = request.data
        client_id = request_data.get('client_id')
        focus_percentage = request_data.get('focus_percentage')
        if client_id is None or focus_percentage is None:
            return Response({'error': 'client_id and focus_percentage are required'},
                            status=status.HTTP_400_BAD_REQUEST)
        if running:
            running = False
            duration_seconds = (datetime.datetime.now() - timer).total_seconds()
            duration_hours = duration_seconds / 3600
            try:
                DailyActivity.create_or_update(datetime.date.today(), focus_percentage, duration_hours,
                                               ClientModel.objects.get(pk=client_id))
                WeeklyActivity.calculate_weekly_activity(ClientModel.objects.get(pk=client_id))
                return Response({'message': 'Screenshot capturing stopped'}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'message': 'Client Not Found'},
                                status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'message': 'Screenshot capturing is not in progress'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({'error': 'Only POST requests are allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


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
@api_view(['GET'])
def client_list(request):
    clients = ClientModel.objects.all()
    serializer = ClientSerializer(clients, many=True)
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

    # Retrieve data from stored weekly activity
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
