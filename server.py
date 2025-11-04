from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

TEXT_MODEL = "llama-3.1-8b-instant"
VISION_MODEL = "llama-3.2-vision-11b"

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def extract_reply(raw):
    """
    ✅ Groq Vision NUEVO FORMATO:
    content = [
        { "type": "output_text", "text": "respuesta" }
    ]
    """
    try:
        content = raw["choices"][0]["message"]["content"]

        # Si ya es texto normal
        if isinstance(content, str):
            return content

        # Si es lista (visión)
        if isinstance(content, list):
            for item in content:
                if item.get("type") == "output_text":
                    return item.get("text")
            return "[No se encontró texto en la respuesta]"

    except:
        return "Error analizando respuesta del modelo."


@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Servidor activo ✅"})


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json

        # ✅ SOLO TEXTO
        if "message" in data and "image" not in data:
            payload = {
                "model": TEXT_MODEL,
                "messages": [
                    {"role": "user", "content": data["message"]}
                ]
            }

        # ✅ TEXTO + IMAGEN (base64)
        elif "image" in data:
            payload = {
                "model": VISION_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": data.get("message", "")},
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
    app.run(host="0.0.0.0", port=10000)
