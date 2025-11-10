from flask import Flask, request, jsonify
import requests
import os
import json

app = Flask(__name__)

# ---------------------------
# CONFIG
# ---------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.1-8b-instant"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)
# ---------------------------


def gemini_describe_image(base64_img, prompt_text):
    """Envía la imagen a Gemini y devuelve el análisis en texto."""
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

    r = requests.post(
        f"{GEMINI_URL}?key={GEMINI_API_KEY}",
        headers={"Content-Type": "application/json"},
        json=payload
    )

    data = r.json()

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except:
        return f"[GeminiError]: {data.get('error', {}).get('message', 'Error desconocido.')}"


def groq_chat(prompt):
    """Envía un mensaje de texto a Groq y devuelve respuesta."""
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}]
    }

    r = requests.post(
        GROQ_URL,
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload
    )

    data = r.json()

    try:
        return data["choices"][0]["message"]["content"]
    except:
        return f"[GroqError]: {data.get('error', {}).get('message', 'Error desconocido.')}"


@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Servidor activo ✅ Opción C: Gemini + Groq"})


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    base64_img = data.get("image")
    user_text = data.get("message", "")

    # ---------------------------
    # ✅ SI HAY IMAGEN
    # ---------------------------
    if base64_img:
        # 1️⃣ Gemini analiza la imagen
        gemini_analysis = gemini_describe_image(
            base64_img,
            user_text if user_text else "Analiza esta imagen en detalle."
        )

        # 2️⃣ Groq razona sobre el análisis
        full_prompt = f"""
El usuario envió una imagen. Esta es la descripción de Gemini:

{gemini_analysis}

Ahora responde de forma útil y detallada.
"""

        final_response = groq_chat(full_prompt)

        return jsonify({"reply": final_response})

    # ---------------------------
    # ✅ SI SOLO HAY TEXTO
    # ---------------------------
    final_response = groq_chat(user_text)
    return jsonify({"reply": final_response})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
