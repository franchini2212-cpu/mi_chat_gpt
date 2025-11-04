from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

TEXT_MODEL = "llama-3.1-8b-instant"
VISION_MODEL = "llama-3.2-11b-vision-preview"

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_VISION_URL = "https://api.groq.com/openai/v1/responses"


def extract_reply_chat(raw):
    try:
        return raw["choices"][0]["message"]["content"]
    except:
        return "Error analizando respuesta (chat)."


def extract_reply_vision(raw):
    try:
        return raw["output_text"]
    except:
        return "Error analizando respuesta (visión)."


@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Servidor activo ✅"})


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json

        # ✅ Solo texto → usar chat/completions
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

            r = requests.post(
                GROQ_CHAT_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=payload
            )

            raw = r.json()

            if "error" in raw:
                return jsonify({"reply": f"ERROR CHAT: {raw['error']}"}), 400

            return jsonify({"reply": extract_reply_chat(raw)})

        # ✅ Imagen → usar /responses
        else:
            payload = {
                "model": VISION_MODEL,
                "input": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": data.get("message", "")},
                            {
                                "type": "input_image",
                                "image_url": f"data:image/jpeg;base64,{data['image']}"
                            }
                        ]
                    }
                ]
            }

            r = requests.post(
                GROQ_VISION_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=payload
            )

            raw = r.json()

            if "error" in raw:
                return jsonify({"reply": f"ERROR VISION: {raw['error']}"}), 400

            return jsonify({"reply": extract_reply_vision(raw)})

    except Exception as e:
        return jsonify({"reply": f"SERVER ERROR: {str(e)}"}), 500
