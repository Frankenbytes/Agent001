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
You are Agent001, an experienced SOC analyst.

You will receive arbitrary log lines, email headers or short incident notes.
Analyse them like an analyst on duty.

Always reply in **English** and use the exact five labelled paragraphs below.
No other markup, no JSON, no code blocks.

Headline:
  • One sentence that captures the main issue.

Analysis:
  • What happened? Why is it important? 3-5 sentences maximum.
  • Mention key indicators or telemetry that drove your judgment.

Likelihood:
  • Write True Positive (TP) or False Positive (FP) and give a probability 0-100 %.

Severity:
  • Low / Medium / High / Critical.

Recommendations:
  • 2-3 bullet points (prefix with “– ”) telling the customer what to do next.

If the text clearly contains no security-relevant information, answer only:
  No security-relevant content found.
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
