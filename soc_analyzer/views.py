from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import json
import requests
from dotenv import load_dotenv
import os
import re

load_dotenv()

# ----------  VERBESSERTES PRE-PROMPT  ----------
PRE_PROMPT = """
You are “Agent001”, a senior SOC analyst.

Task: Analyse the incoming JSON alert and respond in **max 500 tokens**.

Return **EXACTLY TWO SECTIONS** separated by a line with three dashes (`---`):

1️⃣  A single-line JSON object **without line breaks** containing:
    {"class": "...", "subtype": "...", "type": "...",
     "summary": "...", "confidence": 0-100}

    • class  = high-level category (e.g. "ICT Security")  
    • subtype = finer category (e.g. "Malware Detection")  
    • type    = specific nature (e.g. "Network Traffic Anomaly")  
    • summary = ≤15 words main finding  
    • confidence = integer 0-100 (your TP vs FP certainty)

2️⃣  A concise explanatory paragraph (≤250 tokens) that:
    • fixes grammar/typos, writes fluent prose  
    • masks all URLs by replacing “http” → “hxxp”  
    • preserves any metadata bullet-points exactly as given  
    • adds background context, practical recommendations  
    • ends with “TP” or “FP” justification.

No other text, no code-fences, no markdown. Keep strictly to this format.
"""

# ----------  HELFER  ----------
def _clean_request_body(request):
    body_str = request.body.decode("utf-8").strip()
    body_str = re.sub(r"[\n\r\t\x00]+$", "", body_str)
    return json.loads(body_str)

def _build_payload(alert_data: dict):
    ollama_url   = os.getenv("OLLAMA_API_URL")
    ollama_model = os.getenv("OLLAMA_MODEL", "modelq4:latest")

    prompt = f"{PRE_PROMPT}\n\nAlert:\n{json.dumps(alert_data, ensure_ascii=False)}"

    return ollama_url, {
        "model":   ollama_model,
        "prompt":  prompt,
        "stream":  True,
        "options": { "num_predict": 500 }
    }

# ----------  NICHT-STREAMEND ----------
@csrf_exempt
def alert_view(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Only POST requests allowed"}, status=405)

    try:
        data = _clean_request_body(request)
        ollama_url, payload = _build_payload(data)

        r = requests.post(f"{ollama_url}/api/generate", json=payload, stream=True)
        full = "".join(json.loads(l.decode())["response"]
                       for l in r.iter_lines() if l and "response" in json.loads(l.decode()))
        return JsonResponse({"status": "success", "analysis": full})
    except Exception as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=500)

# ----------  STREAMEND ----------
@csrf_exempt
def stream_alert_view(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Only POST requests allowed"}, status=405)

    def gen():
        try:
            data = _clean_request_body(request)
            ollama_url, payload = _build_payload(data)

            with requests.post(f"{ollama_url}/api/generate", json=payload, stream=True) as r:
                for l in r.iter_lines():
                    if not l:
                        continue
                    try:
                        j = json.loads(l.decode())
                        if "response" in j:
                            yield j["response"]
                    except json.JSONDecodeError:
                        continue
        except Exception as exc:
            yield f"\n[ERROR] {exc}"

    return StreamingHttpResponse(
        gen(),
        content_type="text/plain",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

# ----------  CHAT-SEITE ----------
def chat_page(request):
    return render(request, "chat.html")
