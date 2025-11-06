from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

API_KEY = os.getenv("GROQ_API_KEY")
TEXT_MODEL = "llama-3.1-8b-instant"
VISION_MODEL = "llama-3.2-11b-vision-preview"

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def extract_reply(data):
    try:
        return data["choices"][0]["message"]["content"]
    except:
        return "Respuesta inválida del modelo."


@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Servidor activo ✅"})


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()

        # --- Caso texto ---
        if "image" not in data:
            payload = {
                "model": TEXT_MODEL,
                "messages": [
                    {"role": "user", "content": data["message"]}
                ]
            }

        # --- Caso imagen ---
        else:
            payload = {
                "model": VISION_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": data.get("message", "Describe esto")},
                            {"type": "input_image", "image": data["image"]}
                        ]
                    }
                ]
            }

        r = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {API_KEY}"},
            json=payload
        )

        reply = extract_reply(r.json())
        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
