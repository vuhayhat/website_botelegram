import json
from django.http import JsonResponse, HttpResponse
# from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import requests

def chatbot_view(request):
    return render(request, 'chatbot/chatbot.html')