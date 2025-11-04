from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TEXT_MODEL = "llama-3.1-8b-instant"
VISION_MODEL = "llama-3.2-11b-vision-preview"

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def extract_reply(data):
    try:
        msg = data["choices"][0]["message"]["content"]

        if isinstance(msg, str):
            return msg

        if isinstance(msg, list):
            for block in msg:
                if block.get("type") == "output_text":
                    return block.get("text")
        return "No se encontró texto."
    except:
        return "Error analizando respuesta del modelo."


@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Servidor activo ✅"})


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()

        if "message" in data and "image" not in data:
            payload = {
                "model": TEXT_MODEL,
                "messages": [{"role": "user", "content": data["message"]}]
            }

        elif "image" in data:
            payload = {
                "model": VISION_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": data.get("message", "Describe esto")},
                            {"type": "input_image",
                             "image_url": f"data:image/jpeg;base64,{data['image']}"}
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

        # ✅ SOLO ESTO — YA SIN RAW
        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
