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
            # Debug: Log request.body details
            print("Request body (raw):", request.body)
            print("Request body length:", len(request.body))
            print("Request body type:", type(request.body))
            # Explicitly decode bytes to string and strip whitespace
            body_str = request.body.decode('utf-8').strip()
            print("Request body (decoded):", body_str)
            print("Request body (decoded length):", len(body_str))
            print("Request body (decoded repr):", repr(body_str))
            print("Request body (decoded hex):", body_str.encode('utf-8').hex())
            # Additional cleanup: Remove any non-JSON characters
            body_str = body_str.rstrip('\n\r\t\x00')
            print("Request body (cleaned):", body_str)
            data = json.loads(body_str)
            ollama_url = os.getenv('OLLAMA_API_URL')
            ollama_model = os.getenv('OLLAMA_MODEL')
            response = requests.post(
                f"{ollama_url}/api/generate",
                json={"model": ollama_model, "prompt": f"Received alert: {data}"}
            )
            response_data = response.json()
            return JsonResponse({'status': 'success', 'received': data, 'ollama_response': response_data})
        except json.JSONDecodeError as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Invalid JSON: {str(e)}',
                'body': str(request.body),
                'body_decoded': body_str,
                'body_decoded_repr': repr(body_str),
                'body_decoded_hex': body_str.encode('utf-8').hex()
            }, status=400)
        except requests.RequestException as e:
            return JsonResponse({'status': 'error', 'message': f'Ollama API error: {str(e)}'}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Only POST requests allowed'}, status=405)