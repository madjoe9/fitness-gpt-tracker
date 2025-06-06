import openai
import requests
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# API-Key aus Umgebungsvariable
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbwUKaBRfIl4DXS3ikmdDbKD3QV_OlkYYeRYOJwPnESdvpNuLON-jwx0hzkG3RA3_L972Q/exec"

openai.api_key = OPENAI_API_KEY

# GPT Function nur für Gewicht
functions = [
    {
        "name": "send_gewicht",
        "description": "Sendet das aktuelle Gewicht an Google Sheet",
        "parameters": {
            "type": "object",
            "properties": {
                "gewicht": {"type": "string"}
            },
            "required": ["gewicht"]
        }
    }
]

@app.route("/track", methods=["POST"])
def track():
    user_input = request.json.get("eingabe")

    chat = openai.ChatCompletion.create(
        model="gpt-4-0613",
        messages=[{"role": "user", "content": user_input}],
        functions=functions,
        function_call="auto"
    )

    response_message = chat["choices"][0]["message"]

    if "function_call" in response_message:
        import json
        args = json.loads(response_message["function_call"]["arguments"])
        requests.post(WEBHOOK_URL, json=args)
        return jsonify({"status": "✅ Gewicht gesendet", "daten": args})

    return jsonify({"status": "⚠️ Kein Gewicht erkannt"})

@app.route("/", methods=["GET"])
def home():
    return "✅ GPT Gewicht Tracker läuft!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
