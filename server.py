# server.py
from flask import Flask, request, jsonify
from groq import Groq
import os

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("Falta variable de entorno GROQ_API_KEY")

# Crear cliente sin 'proxies' (la versión nueva no acepta ese parámetro)
cliente = Groq(api_key=GROQ_API_KEY)

# helper para extraer texto de respuesta Groq (vision o texto plano)
def extract_text_from_response(raw):
    try:
        content = raw["choices"][0]["message"]["content"]
        # si viene como string
        if isinstance(content, str):
            return content
        # si viene como lista (vision)
        if isinstance(content, list):
            for item in content:
                if item.get("type") in ("output_text", "text"):
                    return item.get("text") or item.get("content") or ""
            return "[No se encontró texto en la respuesta]"
    except Exception as e:
        return f"Error extrayendo respuesta: {e}"

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Servidor activo ✅"}), 200

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)

    # Caso: texto solo
    if "message" in data and "image" not in data:
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "user", "content": data["message"]}
            ]
        }
    # Caso: imagen (base64) + opcional texto
    elif "image" in data:
        user_text = data.get("message", "")
        b64 = data["image"]
        payload = {
            "model": "llama-3.2-vision-11b",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": user_text or "Describe esta imagen"},
                        {"type": "input_image", "image_url": f"data:image/jpeg;base64,{b64}"}
                    ]
                }
            ]
        }
    else:
        return jsonify({"error": "Formato inválido (esperado 'message' o 'image')"}), 400

    # Llamada al API Groq (cliente groq)
    try:
        resp = cliente.chat.completions.create(**payload)
        # resp puede ser objeto con estructura; convertir a dict si es necesario
        raw = resp if isinstance(resp, dict) else resp.__dict__ if hasattr(resp, "__dict__") else resp
        reply = extract_text_from_response(raw)
        return jsonify({"reply": reply, "raw": raw})
    except Exception as e:
        # devuelve el error crudo para debugging (se mostrará en tu app)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
