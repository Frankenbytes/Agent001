from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import requests
from dotenv import load_dotenv
import os
import re

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
            # Stricter cleanup: Remove all non-JSON characters after JSON object
            body_str = re.sub(r'[\n\r\t\x00]+$', '', body_str)
            print("Request body (cleaned):", body_str)
            print("Request body (cleaned length):", len(body_str))
            print("Request body (cleaned repr):", repr(body_str))
            print("Request body (cleaned hex):", body_str.encode('utf-8').hex())
            # Try parsing JSON
            data = json.loads(body_str)
            print("Parsed data:", data)
            # Debug: Log environment variables
            ollama_url = os.getenv('OLLAMA_API_URL')
            ollama_model = os.getenv('OLLAMA_MODEL')
            print("OLLAMA_API_URL:", ollama_url)
            print("OLLAMA_MODEL:", ollama_model)
            # Debug: Log request payload
            request_payload = {"model": ollama_model, "prompt": f"Received alert: {data}"}
            print("Request payload to Ollama:", request_payload)
            response = requests.post(
                f"{ollama_url}/api/generate",
                json=request_payload,
                stream=True
            )
            print("Ollama response status:", response.status_code)
            # Process streaming response
            full_response = ""
            response_data = []
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    print("Ollama response line:", decoded_line)
                    try:
                        json_line = json.loads(decoded_line)
                        response_data.append(json_line)
                        if 'response' in json_line:
                            full_response += json_line['response']
                    except json.JSONDecodeError as e:
                        print("Failed to parse response line:", decoded_line, "Error:", str(e))
            print("Ollama full response text:", full_response)
            print("Ollama response data:", response_data)
            return JsonResponse({
                'status': 'success',
                'received': data,
                'ollama_response': {'response': full_response, 'details': response_data}
            })
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
            return JsonResponse({
                'status': 'error',
                'message': f'Ollama API error: {str(e)}',
                'response_status': getattr(e.response, 'status_code', None),
                'response_text': getattr(e.response, 'text', None)
            }, status=500)
    return JsonResponse({'status': 'error', 'message': 'Only POST requests allowed'}, status=405)