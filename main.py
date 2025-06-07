import openai
import requests
from flask import Flask, request, jsonify
import os
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)  # Erlaubt CORS-Zugriff von außen

# Deine OpenAI API und Google Sheets Webhook
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbwUKaBRfIl4DXS3ikmdDbKD3QV_OlkYYeRYOJwPnESdvpNuLON-jwx0hzkG3RA3_L972Q/exec"

openai.api_key = OPENAI_API_KEY

# GPT-Funktion, die Tagesdaten erwartet
functions = [
    {
        "name": "send_daily_data",
        "description": "Sendet die Tagesdaten an Google Sheet",
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
            "required": ["gewicht"]
        }
    }
]

# Haupt-Endpunkt für GPT-Daten
@app.route("/track", methods=["POST"])
def track():
    user_input = request.json.get("eingabe")
    print("📥 Eingabe vom Client:", user_input)

    try:
        chat = openai.ChatCompletion.create(
            model="gpt-4o",      # ✅ neu,  # oder gpt-4-0613 wenn verfügbar
            messages=[{"role": "user", "content": user_input}],
            functions=functions,
            function_call="auto"
        )
    except Exception as e:
        print("❌ GPT-Fehler:", str(e))
        return jsonify({"error": "GPT-Aufruf fehlgeschlagen", "details": str(e)}), 500

    response_message = chat["choices"][0]["message"]
    print("🤖 GPT-Antwort:", response_message)

    if "function_call" in response_message:
        try:
            args = json.loads(response_message["function_call"]["arguments"])
            print("📤 Wird gesendet an Google Sheet:", args)
            gsheet_response = requests.post(WEBHOOK_URL, json=args)
            print("📬 Antwort von Google Sheet:", gsheet_response.status_code, gsheet_response.text)

            if gsheet_response.status_code == 200 and "success" in gsheet_response.text.lower():
                return jsonify({"status": "✅ Daten gespeichert!", "daten": args})
            else:
                return jsonify({
                    "status": "⚠️ Fehler beim Speichern",
                    "details": gsheet_response.text
                }), 500

        except Exception as e:
            print("❌ Fehler beim Verarbeiten:", str(e))
            return jsonify({"error": "Verarbeitung der GPT-Daten fehlgeschlagen", "details": str(e)}), 500

    print("⚠️ Keine function_call enthalten")
    return jsonify({"status": "⚠️ Keine gültigen Daten erkannt", "antwort": response_message})

# Test-Endpunkt für Render-Check
@app.route("/", methods=["GET"])
def home():
    return "✅ GPT-Tracker läuft im Debug-Modus"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
