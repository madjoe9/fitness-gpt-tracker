import openai
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# === SETUP ===
import os
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbwUKaBRfIl4DXS3ikmdDbKD3QV_OlkYYeRYOJwPnESdvpNuLON-jwx0hzkG3RA3_L972Q/exec"

openai.api_key = OPENAI_API_KEY

# === FUNKTIONEN ===
functions = [
    {
        "name": "send_daily_data",
        "description": "Sende Tagesdaten an Google Sheet",
        "parameters": {
            "type": "object",
            "properties": {
                "gewicht": {"type": "string"},
                "frühstück": {"type": "string"},
                "mittagessen": {"type": "string"},
                "abendessen": {"type": "string"},
                "bewegung": {"type": "string"},
                "stimmung": {"type": "string"}
            },
            "required": ["gewicht", "frühstück", "mittagessen", "abendessen", "bewegung", "stimmung"]
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
        args = response_message["function_call"]["arguments"]
        data = eval(args)  # Konvertiert String zu dict (vorsichtig!)
        requests.post(WEBHOOK_URL, json=data)
        return jsonify({"status": "✅ Daten gesendet", "daten": data})

    return jsonify({"status": "⚠️ Keine Daten erkannt"})

@app.route("/", methods=["GET"])
def home():
    return "✅ GPT Fitness Tracker läuft!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
