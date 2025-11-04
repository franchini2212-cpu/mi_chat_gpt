from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

TEXT_MODEL = "llama-3.1-8b-instant"
VISION_MODEL = "llama-3.2-11b-vision-preview"

CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
VISION_URL = "https://api.groq.com/openai/v1/responses"


# ✅ Extrae respuesta del modelo de texto
def extract_chat(raw):
    try:
        return raw["choices"][0]["message"]["content"]
    except:
        return f"RAW: {raw}"


# ✅ Extrae respuesta del modelo de visión
def extract_vision(raw):
    try:
        return raw["output"][0]["content"][0]["text"]
    except:
        try:
            return raw["output_text"]
        except:
            return f"RAW: {raw}"


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

        raw = r.json()
        return jsonify({"reply": extract_chat(raw)})

    # ✅ TEXTO + IMAGEN
    else:
        base64_img = data["image"]

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
                            "image_url": f"data:image/jpeg;base64,{base64_img}"
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

        raw = r.json()
        return jsonify({"reply": extract_vision(raw)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
