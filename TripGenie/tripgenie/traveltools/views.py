import requests
from django.http import JsonResponse
from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.decorators import login_required
from .models import ToolUsage
from datetime import datetime
import pytz
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@login_required(login_url='/login')
def tools(request):
    """Render the all-in-one tools dashboard"""
    return render(request, "tools.html")


@csrf_exempt
@login_required(login_url='/login')
def convert_currency(request):
    from_currency = request.GET.get("from")
    to_currency = request.GET.get("to")
    amount = float(request.GET.get("amount", 1))

    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
        res = requests.get(url)
        data = res.json()
        rate = data["rates"].get(to_currency)

        if not rate:
            return JsonResponse({"error": "Invalid currency code."}, status=400)

        converted = round(amount * rate, 2)

        ToolUsage.objects.create(
            user=request.user,
            tool_type="currency",
            query=f"{amount} {from_currency} to {to_currency}",
            result=str(converted),
        )

        return JsonResponse({
            "amount": amount,
            "from": from_currency,
            "to": to_currency,
            "converted": converted,
            "rate": rate
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@login_required(login_url='/login')
def get_weather(request):
    city = request.GET.get("city")
    api_key = "your_weather_api_key"  # WeatherAPI.com key

    try:
        url = f"https://api.weatherapi.com/v1/current.json?key={api_key}&q={city}&aqi=yes"
        response = requests.get(url, timeout=10)
        data = response.json()

        if response.status_code != 200:
            error_msg = data.get('error', {}).get('message', 'Weather data not found')
            return JsonResponse({"error": error_msg}, status=response.status_code)

        current = data['current']
        location = data['location']

        weather = {
            "city": f"{location['name']}, {location['country']}",
            "temperature": current['temp_c'],
            "feels_like": current['feelslike_c'],
            "humidity": current['humidity'],
            "wind_speed": current['wind_kph'],
            "description": current['condition']['text'],
            "uv": current['uv'],
            "visibility": current['vis_km'],
            "air_quality": current.get('air_quality', {}).get('us-epa-index', 'N/A'),
            "localtime": location['localtime'],
        }

        ToolUsage.objects.create(
            user=request.user,
            tool_type="weather",
            query=city,
            result=str(weather),
        )

        return JsonResponse(weather)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@login_required(login_url='/login')
def get_timezone(request):
    tz_name = request.GET.get("timezone")
    try:
        tz = pytz.timezone(tz_name)
        now = datetime.now(tz)
        current_time = now.strftime("%Y-%m-%d %H:%M:%S")

        ToolUsage.objects.create(
            user=request.user,
            tool_type="timezone",
            query=tz_name,
            result=current_time,
        )
        return JsonResponse({"timezone": tz_name, "time": current_time})
    except Exception:
        return JsonResponse({"error": "Invalid timezone."}, status=400)
