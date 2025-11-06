import os

# ✅ QUITAR PROXIES DE RENDER ANTES DE TODO
for proxy in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
    if proxy in os.environ:
        del os.environ[proxy]

from flask import Flask, request, jsonify
from groq import Groq

app = Flask(__name__)

# ✅ Inicializamos Groq sin proxies
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

        # ✅ Solo mensaje
        if "image" not in data:
            completion = client.chat.completions.create(
                model=TEXT_MODEL,
                messages=[{"role": "user", "content": data["message"]}]
            )

        # ✅ Mensaje + imagen
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
