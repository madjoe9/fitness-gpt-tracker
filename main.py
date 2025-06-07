import openai
import requests
from flask import Flask, request, jsonify
import os
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbwUKaBRfIl4DXS3ikmdDbKD3QV_OlkYYeRYOJwPnESdvpNuLON-jwx0hzkG3RA3_L972Q/exec"
openai.api_key = OPENAI_API_KEY

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

@app.route("/track", methods=["POST"])
def track():
    try:
        user_input = request.json.get("eingabe")
        print("📥 Eingabe vom Client:", user_input)

        chat = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": user_input}],
            functions=functions,
            function_call="auto"
        )

        response_message = chat["choices"][0]["message"]
        print("🤖 GPT-Antwort (roh):", response_message)

        if "function_call" in response_message:
            print("🔧 Verarbeite function_call...")

            try:
                arguments_raw = response_message["function_call"]["arguments"]
                print("📦 Rohdaten der arguments:", arguments_raw)

                args = json.loads(arguments_raw)
                print("📤 Sende an Google Sheets:", args)

                gsheet_response = requests.post(WEBHOOK_URL, json=args)
                print("📬 Antwort von Google Sheet:", gsheet_response.status_code, gsheet_response.text)

                if gsheet_response.status_code == 200:
                    return jsonify({"status": "✅ Daten gespeichert!", "details": gsheet_response.text})
                else:
                    return jsonify({
                        "status": "⚠️ Fehler beim Speichern",
                        "details": gsheet_response.text
                    }), 500

            except Exception as parse_err:
                print("❌ Fehler beim Parsen:", str(parse_err))
                return jsonify({
                    "error": "Fehler beim Verarbeiten der GPT-Daten",
                    "details": str(parse_err)
                }), 500

        print("⚠️ Keine function_call enthalten")
        return jsonify({"status": "⚠️ Keine gültigen Daten erkannt", "antwort": str(response_message)})

    except Exception as main_err:
        print("❌ Allgemeiner Fehler:", str(main_err))
        return jsonify({"error": "Unerwarteter Fehler", "details": str(main_err)}), 500

@app.route("/", methods=["GET"])
def home():
    return "✅ GPT-Tracker läuft im Debug-Modus"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
