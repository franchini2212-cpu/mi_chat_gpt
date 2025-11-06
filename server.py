from flask import Flask, request, jsonify
from groq import Groq
import os

app = Flask(__name__)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

TEXT_MODEL = "llama-3.1-8b-instant"
VISION_MODEL = "llama-3.2-11b-vision-preview"

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Servidor activo ✅"})

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()

        # ✅ Solo texto
        if "image" not in data:
            completion = client.chat.completions.create(
                model=TEXT_MODEL,
                messages=[{"role": "user", "content": data["message"]}]
            )

        # ✅ Texto + Imagen
        else:
            completion = client.chat.completions.create(
                model=VISION_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": data.get("message", "Describe la imagen")},
                            {
                                "type": "input_image",
                                "image_url": f"data:image/png;base64,{data['image']}"
                            }
                        ]
                    }
                ]
            )

        reply = completion.choices[0].message.content
        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
