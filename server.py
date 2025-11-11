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
    """Analiza imagen con Gemini y devuelve el texto."""
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


def groq_chat(messages):
    """Envía historial completo a Groq y devuelve respuesta."""
    payload = {
        "model": GROQ_MODEL,
        "messages": messages
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
    return jsonify({"status": "Servidor activo ✅ con historial"})


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    base64_img = data.get("image")
    user_text = data.get("message", "")

    # ✅ HISTORIAL COMPLETO que envía la app
    history = data.get("history", [])

    groq_messages = []

    # -------------------------------------------------
    # ✅ Convertimos historial al formato que Groq entiende
    # -------------------------------------------------
    for h in history:

        # ✅ 1) Si es texto, lo pasamos directo
        if "content" in h and h["content"]:
            groq_messages.append({
                "role": h["role"],
                "content": h["content"]
            })

        # ✅ 2) Si hubo imagen antes, la analizamos con Gemini
        elif "image" in h and h["image"]:
            gemini_analysis = gemini_describe_image(
                h["image"],
                "Describe esta imagen enviada antes."
            )
            groq_messages.append({
                "role": h["role"],
                "content": (
                    "[Imagen enviada anteriormente]\n\n"
                    f"Análisis por Gemini:\n{gemini_analysis}"
                )
            })

    # -------------------------------------------------
    # ✅ USUARIO ENVÍA UNA IMAGEN AHORA
    # -------------------------------------------------
    if base64_img:

        # 1) Analizar imagen con Gemini
        gemini_analysis = gemini_describe_image(
            base64_img,
            user_text if user_text else "Analiza esta imagen."
        )

        # 2) Guardamos ese análisis para Groq
        groq_messages.append({
            "role": "user",
            "content": (
                "El usuario envió una nueva imagen.\n\n"
                f"Análisis por Gemini:\n{gemini_analysis}"
            )
        })

        # 3) Groq responde usando TODO el historial
        final = groq_chat(groq_messages)
        return jsonify({"reply": final})

    # -------------------------------------------------
    # ✅ USUARIO ENVÍA SOLO TEXTO
    # -------------------------------------------------
    groq_messages.append({
        "role": "user",
        "content": user_text
    })

    final = groq_chat(groq_messages)
    return jsonify({"reply": final})


# ✅ NECESARIO PARA RENDER
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
