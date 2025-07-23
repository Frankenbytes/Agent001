from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import requests
from dotenv import load_dotenv
import os

load_dotenv()

@csrf_exempt
def alert_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ollama_url = os.getenv('OLLAMA_API_URL')
            ollama_model = os.getenv('OLLAMA_MODEL')
            response = requests.post(
                f"{ollama_url}/api/generate",
                json={"model": ollama_model, "prompt": f"Received alert: {data}"}
            )
            response_data = response.json()
            return JsonResponse({'status': 'success', 'received': data, 'ollama_response': response_data})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except requests.RequestException as e:
            return JsonResponse({'status': 'error', 'message': f'Ollama API error: {str(e)}'}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Only POST requests allowed'}, status=405)