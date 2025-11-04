from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

TEXT_MODEL = "llama-3.1-8b-instant"
VISION_MODEL = "llama-3.2-11b-vision-preview"

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def extract_reply(raw):
    try:
        return raw["choices"][0]["message"]["content"]
    except:
        return "Error analizando respuesta del modelo."


@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Servidor activo ✅"})


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json

        # ✅ Mensaje solo texto
        if "image" not in data:
            payload = {
                "model": TEXT_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": data["message"]
                    }
                ]
            }

        # ✅ Mensaje con imagen base64
        else:
            payload = {
                "model": VISION_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": data.get("message", ""),
                        "images": [data["image"]]  # base64 directo
                    }
                ]
            }

        r = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload
        )

        raw = r.json()

        if "error" in raw:
            return jsonify({"reply": f"ERROR GROQ: {raw['error']}"}), 400

        return jsonify({"reply": extract_reply(raw)})

    except Exception as e:
        return jsonify({"reply": f"ERROR SERVER: {str(e)}"}), 500
