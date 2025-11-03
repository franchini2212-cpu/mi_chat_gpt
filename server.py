import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_ID = os.getenv("MODEL_ID", "llama3-8b-8192")  # ✅ Modelo real de Groq
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"

if not GROQ_API_KEY:
    raise RuntimeError("Falta la variable de entorno GROQ_API_KEY")

@app.route("/", methods=["GET"])
def home():
    return "Servidor funcionando con Groq ✅"

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)

    messages = data.get("messages")
    if not messages:
        user_msg = data.get("message")
        if not user_msg:
            return jsonify({"error": "Falta mensaje"}), 400
        messages = [{"role": "user", "content": user_msg}]

    body = {
        "model": MODEL_ID,
        "messages": messages
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    r = requests.post(GROQ_CHAT_URL, json=body, headers=headers)
    return jsonify(r.json())

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
