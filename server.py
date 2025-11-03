import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# Si quieres probar otro modelo más adelante, ponlo en Render como variable MODEL_ID
MODEL_ID = os.getenv("MODEL_ID", "llama-3.1-8b-instant")
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"

if not GROQ_API_KEY:
    raise RuntimeError("Falta la variable de entorno GROQ_API_KEY")

@app.route("/", methods=["GET"])
def home():
    return "Servidor funcionando con Groq ✅"

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(force=True)

        # Aceptamos dos formatos:
        # 1) {"message": "hola"}
        # 2) {"messages": [{ "role": "user", "content": "hola" }, ...]}
        messages = data.get("messages")
        if not messages:
            user_msg = data.get("message")
            if not user_msg:
                return jsonify({"error": "Falta 'message' o 'messages' en el body"}), 400
            messages = [{"role": "user", "content": user_msg}]

        body = {
            "model": MODEL_ID,
            "messages": messages
        }

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        r = requests.post(GROQ_CHAT_URL, json=body, headers=headers, timeout=60)
        r.raise_for_status()
        resp_json = r.json()

        # Intentamos devolver un campo simple "reply" con el texto de la respuesta
        try:
            reply = resp_json["choices"][0]["message"]["content"]
        except Exception:
            # si viene otro formato, devolvemos toda la respuesta cruda
            return jsonify({"raw": resp_json})

        return jsonify({"reply": reply, "raw": resp_json})
    except requests.exceptions.HTTPError as he:
        return jsonify({"error": "HTTP error al llamar a Groq", "detail": str(he), "resp": getattr(he, "response", None).text if getattr(he, "response", None) else None}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
