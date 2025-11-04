from flask import Flask, request, jsonify
from groq import Groq
import base64
import os

app = Flask(__name__)
client = Groq(api_key=os.environ["GROQ_API_KEY"])

@app.route("/", methods=["GET"])
def home():
    return "✅ Servidor activo"

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()

        # ------------------------------
        # ✅ SI VIENE TEXTO
        # ------------------------------
        if "message" in data:
            text = data["message"]

            completion = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "user", "content": text}
                ]
            )

            reply = completion.choices[0].message["content"]
            return jsonify({"reply": reply})

        # ------------------------------
        # ✅ SI VIENE IMAGEN BASE64
        # ------------------------------
        if "image" in data:
            b64 = data["image"]

            # Groq Vision necesita esto:
            msg = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe la imagen"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": "data:image/jpeg;base64," + b64
                            }
                        }
                    ]
                }
            ]

            completion = client.chat.completions.create(
                model="llama-vision",
                messages=msg
            )

            raw = completion  # <-- Para debug
            reply = completion.choices[0].message["content"]

            return jsonify({
                "reply": reply,
                "raw": raw.dict()  # Muestra TODO para debug
            })

        # ------------------------------
        # ❌ Si no trae nada válido
        # ------------------------------
        return jsonify({"error": "Invalid request"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
