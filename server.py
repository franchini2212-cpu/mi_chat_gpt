from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TEXT_MODEL = "llama-3.1-8b-instant"
VISION_MODEL = "llama-3.2-11b-vision-preview"

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def extract_reply(data):
    """
    Extrae texto de modelos normales y vision.
    """
    try:
        msg = data["choices"][0]["message"]["content"]

        # Respuesta tipo string (texto normal)
        if isinstance(msg, str):
            return msg

        # Respuesta tipo lista (Vision)
        if isinstance(msg, list):
            for block in msg:
                if block.get("type") == "output_text":
                    return block.get("text")
        return "[No se encontró texto]"
    except:
        return "Error analizando respuesta del modelo."


@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Servidor activo ✅"})


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()

        # ✅ Texto
        if "message" in data and "image" not in data:
            payload = {
                "model": TEXT_MODEL,
                "messages": [
                    {"role": "user", "content": data["message"]}
                ]
            }

        # ✅ Imagen base64
        elif "image" in data:
            payload = {
                "model": VISION_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": data.get("message", "Describe esto")},
                            {
                                "type": "input_image",
                                "image_url": f"data:image/jpeg;base64,{data['image']}"
                            }
                        ]
                    }
                ]
            }

        else:
            return jsonify({"error": "Formato inválido"}), 400

        # ✅ Llamada a Groq con requests
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

        return jsonify({"reply": reply, "raw": raw})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
