from flask import Flask, request, jsonify
import requests
import os
import logging

# ✅ Logging para ver errores reales en Render
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# ✅ Modelos Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TEXT_MODEL = "llama-3.1-8b-instant"
VISION_MODEL = "llama-3.2-11b-vision-preview"

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


# ✅ EXTRACT REPLY SUPER ROBUSTO
def extract_reply(data):
    try:
        if not data or "choices" not in data or len(data["choices"]) == 0:
            logging.info("Respuesta sin choices")
            logging.info(f"RAW: {data}")
            return "Respuesta inválida del modelo."

        content = data["choices"][0]["message"]["content"]

        # ✅ Caso simple (string)
        if isinstance(content, str):
            return content

        # ✅ Caso lista de bloques (Vision)
        if isinstance(content, list):
            textos = []
            for block in content:
                tipo = block.get("type")

                # Groq Vision puede devolver: output_text, text, o otros
                if tipo in ["output_text", "text"]:
                    t = block.get("text")
                    if t:
                        textos.append(t)

            if textos:
                return " ".join(textos)

        logging.info("No se pudo extraer texto, RAW:")
        logging.info(data)
        return "No pude extraer texto de la respuesta."

    except Exception as e:
        logging.exception("Error en extract_reply")
        return f"Error en extract_reply: {str(e)}"


# ✅ RUTA PRINCIPAL
@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Servidor activo ✅"})


# ✅ RUTA DE CHAT (texto o imagen)
@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()

        # ✅ TEXTO NORMAL
        if "message" in data and "image" not in data:
            payload = {
                "model": TEXT_MODEL,
                "messages": [
                    {"role": "user", "content": data["message"]}
                ]
            }

        # ✅ IMAGEN + mensaje opcional
        elif "image" in data:
            payload = {
                "model": VISION_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": data.get("message", "Describe esta imagen")},
                            {"type": "input_image",
                             "image_url": f"data:image/jpeg;base64,{data['image']}"}
                        ]
                    }
                ]
            }

        else:
            return jsonify({"error": "Formato inválido"}), 400

        # ✅ Llamada a Groq
        r = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload
        )

        raw = r.json()
        reply = extract_reply(raw)

        return jsonify({"reply": reply})

    except Exception as e:
        logging.exception("Error en /chat")
        return jsonify({"reply": f"Error: {str(e)}"})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
