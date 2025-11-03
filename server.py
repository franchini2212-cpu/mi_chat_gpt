import os
from flask import Flask, request, jsonify
import requests
import base64

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_ID = "llama-3.2-11b-vision-preview"
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"

if not GROQ_API_KEY:
    raise RuntimeError("Falta GROQ_API_KEY")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)

    user_text = data.get("message", "")
    image_b64 = data.get("image", None)   # ← AQUI RECIBE LA IMAGEN EN BASE64

    messages = []

    if image_b64:
        messages.append({
            "role": "user",
            "content": [
                {"type": "input_text", "text": user_text},
                {"type": "input_image", "image_url": f"data:image/jpeg;base64,{image_b64}"}
            ]
        })
    else:
        messages.append({"role": "user", "content": user_text})

    body = {
        "model": MODEL_ID,
        "messages": messages
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    r = requests.post(GROQ_CHAT_URL, json=body, headers=headers)
    result = r.json()

    # Extraer respuesta
    try:
        reply = result["choices"][0]["message"]["content"]
    except:
        reply = "Error analizando respuesta del modelo."

    return jsonify({
        "reply": reply,
        "raw": result
    })

@app.route("/", methods=["GET"])
def root():
    return "Servidor activo ✅"

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
