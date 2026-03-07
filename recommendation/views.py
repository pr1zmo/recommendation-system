from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse
import json

def home(request):
    return render(request, 'index.html')


def data_json(request):
    data_path = settings.BASE_DIR / "data.json"

    with data_path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    return JsonResponse(payload)
