from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

TEXT_MODEL = "llama-3.1-8b-instant"
VISION_MODEL = "llama-3.2-vision-11b"

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def extract_reply(raw):
    try:
        content = raw["choices"][0]["message"]["content"]

        if isinstance(content, str):
            return content

        if isinstance(content, list):
            for item in content:
                if item.get("type") == "output_text":
                    return item.get("text")

        return "No se encontró texto en la respuesta."

    except Exception as e:
        return f"ERROR EXTRACTION: {str(e)}"


@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Servidor activo ✅"})


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json

        # ✅ SOLO TEXTO
        if "image" not in data:
            payload = {
                "model": TEXT_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": data["message"]}
                        ]
                    }
                ]
            }

        # ✅ TEXTO + IMAGEN
        else:
            payload = {
                "model": VISION_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": data.get("message", "")},
                            {
                                "type": "image_url",
                                "image_url": f"data:image/jpeg;base64,{data['image']}"
                            }
                        ]
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

        respuesta = extract_reply(raw)
        return jsonify({"reply": respuesta})

    except Exception as e:
        return jsonify({"reply": f"ERROR SERVER: {str(e)}"}), 500
