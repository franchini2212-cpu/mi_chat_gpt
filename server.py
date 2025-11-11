# server.py
from flask import Flask, request, jsonify
import os
import requests
import psycopg2
import psycopg2.extras
import json
import traceback
from datetime import datetime

app = Flask(__name__)

# ---------------------------
# CONFIG desde ENV
# ---------------------------
DB_URL = os.getenv("DB_URL")  # ej: postgresql://user:pass@host:5432/dbname
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Validaciones simples
if not DB_URL:
    raise RuntimeError("DB_URL no está definida en las env vars.")
if not GEMINI_API_KEY:
    app.logger.warning("GEMINI_API_KEY no definida; las llamadas a Gemini fallarán.")
if not GROQ_API_KEY:
    app.logger.warning("GROQ_API_KEY no definida; las llamadas a Groq fallarán.")


# ---------------------------
# Util: conexión por request
# ---------------------------
def get_db():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    return conn, cur


# ---------------------------
# Inicializar tabla(s) (llamado una vez)
# ---------------------------
def init_db():
    conn, cur = get_db()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id SERIAL PRIMARY KEY,
            user_id TEXT NOT NULL,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT,
            image_base64 TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)
    conn.commit()
    conn.close()


init_db()


# ---------------------------
# Guardar / recuperar mensajes
# ---------------------------
def guardar_mensaje(user_id, conversation_id, role, content=None, image_base64=None):
    conn, cur = get_db()
    cur.execute(
        "INSERT INTO conversations (user_id, conversation_id, role, content, image_base64) VALUES (%s, %s, %s, %s, %s)",
        (user_id, conversation_id, role, content, image_base64)
    )
    conn.commit()
    conn.close()


def cargar_historial_db(conversation_id):
    conn, cur = get_db()
    cur.execute(
        "SELECT role, content, image_base64, created_at FROM conversations WHERE conversation_id = %s ORDER BY id ASC",
        (conversation_id,)
    )
    rows = cur.fetchall()
    conn.close()

    historial = []
    for r in rows:
        if r["image_base64"]:
            historial.append({
                "role": r["role"],
                "image": r["image_base64"],
                "created_at": r["created_at"].isoformat()
            })
        else:
            historial.append({
                "role": r["role"],
                "content": r["content"],
                "created_at": r["created_at"].isoformat()
            })
    return historial


# ---------------------------
# Gemini: enviar imagen y prompt, devolver texto
# ---------------------------
def gemini_describe_image(base64_img, prompt_text):
    # payload según API de Generative Language (HTTP)
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt_text},
                    {
                        "inlineData": {
                            "mimeType": "image/jpeg",
                            "data": base64_img
                        }
                    }
                ]
            }
        ],
        "generationConfig": {"responseMimeType": "text/plain"}
    }

    try:
        r = requests.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=60
        )
        data = r.json()
        # buscar la respuesta de texto
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            app.logger.error("Gemini response unexpected: %s", json.dumps(data))
            return f"[GeminiError]: {data.get('error', {}).get('message', 'Respuesta inesperada de Gemini')}"
    except Exception as e:
        app.logger.error("Gemini request failed: %s", str(e))
        return f"[GeminiException]: {str(e)}"


# ---------------------------
# Groq: enviar historial y obtener reply
# ---------------------------
def groq_chat(messages):
    payload = {
        "model": GROQ_MODEL,
        "messages": messages
    }
    try:
        r = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60
        )
        data = r.json()
        try:
            return data["choices"][0]["message"]["content"]
        except Exception:
            app.logger.error("Groq response unexpected: %s", json.dumps(data))
            return f"[GroqError]: {data.get('error', {}).get('message', 'Respuesta inesperada de Groq')}"
    except Exception as e:
        app.logger.error("Groq request failed: %s", str(e))
        return f"[GroqException]: {str(e)}"


# ---------------------------
# Endpoints
# ---------------------------

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "ok", "time": datetime.utcnow().isoformat()})


@app.route("/chat", methods=["POST"])
def chat():
    """
    Body JSON esperada:
    {
      "user_id": "usuario123",            # opcional (recomendado)
      "conversation_id": "conv-abc",      # opcional (se genera si falta)
      "message": "texto"                  # opcional
      "image": "BASE64..."                # opcional
      "prompt": "texto adicional"         # opcional (para Gemini)
    }
    """
    try:
        data = request.get_json(force=True)
        user_id = data.get("user_id", "anonymous")
        conversation_id = data.get("conversation_id") or f"default-{user_id}"
        user_text = data.get("message", "")
        base64_img = data.get("image")
        prompt = data.get("prompt", "")

        # 1) cargar historial de DB y convertir a mensajes para Groq
        history = cargar_historial_db(conversation_id)
        groq_messages = []

        for h in history:
            if "content" in h:
                groq_messages.append({"role": h["role"], "content": h["content"]})
            elif "image" in h:
                # analizar imagen previa solo si no hay análisis guardado como content
                analysis = gemini_describe_image(h["image"], "Describe esta imagen enviada anteriormente.")
                groq_messages.append({"role": h["role"], "content": f"[Imagen previa analizada]:\n{analysis}"})

        # 2) Si hay imagen nueva: analizar, guardar y preparar mensaje para Groq
        if base64_img:
            # analiza con Gemini
            gemini_analysis = gemini_describe_image(base64_img, prompt or (user_text or "Analiza esta imagen."))
            # guardar la imagen (rol=user)
            guardar_mensaje(user_id, conversation_id, "user", None, base64_img)
            # guardar el análisis como un mensaje system (o assistant según prefieras)
            guardar_mensaje(user_id, conversation_id, "system", gemini_analysis, None)
            # añadir al flujo de Groq
            groq_messages.append({"role": "user", "content": f"El usuario envió una imagen. Análisis por Gemini:\n{gemini_analysis}"})

            # obtener respuesta de Groq
            final = groq_chat(groq_messages)

            # guardar respuesta de assistant
            guardar_mensaje(user_id, conversation_id, "assistant", final, None)

            return jsonify({"reply": final, "conversation_id": conversation_id})

        # 3) Si solo texto: guardar y preguntar a Groq
        # añadir el nuevo texto al flujo
        if user_text:
            guardar_mensaje(user_id, conversation_id, "user", user_text, None)
            groq_messages.append({"role": "user", "content": user_text})

        final = groq_chat(groq_messages)

        if final:
            guardar_mensaje(user_id, conversation_id, "assistant", final, None)

        return jsonify({"reply": final, "conversation_id": conversation_id})

    except Exception as e:
        tb = traceback.format_exc()
        app.logger.error("Chat error: %s\n%s", str(e), tb)
        return jsonify({"error": str(e), "trace": tb}), 500


@app.route("/history/<conversation_id>", methods=["GET"])
def get_history(conversation_id):
    try:
        hist = cargar_historial_db(conversation_id)
        return jsonify({"conversation_id": conversation_id, "history": hist})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/conversations/<user_id>", methods=["GET"])
def list_conversations(user_id):
    try:
        conn, cur = get_db()
        cur.execute(
            "SELECT DISTINCT conversation_id, MIN(created_at) as started_at FROM conversations WHERE user_id = %s GROUP BY conversation_id ORDER BY started_at DESC",
            (user_id,)
        )
        rows = cur.fetchall()
        conn.close()
        result = [{"conversation_id": r["conversation_id"], "started_at": r["started_at"].isoformat()} for r in rows]
        return jsonify({"user_id": user_id, "conversations": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
