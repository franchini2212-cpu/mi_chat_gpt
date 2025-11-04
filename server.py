from flask import Flask, request, jsonify
from groq import Groq
import os

app = Flask(__name__)

API_KEY = os.environ.get("GROQ_API_KEY")

cliente = Groq(api_key=API_KEY)

@app.route("/", methods=["GET"])
def home():
    return "✅ Servidor activo", 200


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()

    # -----------------------------------------
    # Si viene TEXTO
    # -----------------------------------------
    if "message" in data:
        user_msg = data["message"]

        respuesta = cliente.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[
                {"role": "user", "content": user_msg}
            ]
        )

        reply = respuesta.choices[0].message.content
        return jsonify({"reply": reply})

    # -----------------------------------------
    # Si viene IMAGEN BASE64
    # -----------------------------------------
    if "image" in data:
        b64 = data["image"]

        respuesta = cliente.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": "Describe esta imagen"},
                        {"type": "input_image", "image_url": f"data:image/jpeg;base64,{b64}"}
                    ]
                }
            ]
        )

        reply = respuesta.choices[0].message.content
        return jsonify({"reply": reply})

    return jsonify({"reply": "Solicitud inválida"}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
