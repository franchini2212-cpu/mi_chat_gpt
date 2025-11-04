from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

TEXT_MODEL = "llama-3.1-8b-instant"
VISION_MODEL = "llama-3.2-11b-vision-preview"

CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
VISION_URL = "https://api.groq.com/openai/v1/responses"


def extract_vision(raw):
    try:
        return raw["output"][0]["content"][0]["text"]
    except:
        return str(raw)


def extract_text(raw):
    try:
        return raw["choices"][0]["message"]["content"]
    except:
        return str(raw)


@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "servidor activo ✅"})


@app.route("/chat", methods=["POST"])
def chat():
    data = request.json

    # ✅ SOLO TEXTO
    if "image" not in data:
        payload = {
            "model": TEXT_MODEL,
            "messages": [
                {"role": "user", "content": data["message"]}
            ]
        }

        r = requests.post(
            CHAT_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload
        )

        return jsonify({"reply": extract_text(r.json())})

    # ✅ TEXTO + IMAGEN (VISIÓN)
    else:
        base64_data = data["image"]

        payload = {
            "model": VISION_MODEL,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": data.get("message", "")
                        },
                        {
                            "type": "input_image",
                            "data": base64_data  # ← AQUÍ VA SOLO EL BASE64
                        }
                    ]
                }
            ]
        }

        r = requests.post(
            VISION_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload
        )

        return jsonify({"reply": extract_vision(r.json())})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
