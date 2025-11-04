from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

TEXT_MODEL = "llama-3.1-8b-instant"
VISION_MODEL = "llama-3.2-vision-11b"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Servidor activo ✅"})


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json

        # ✅ SOLO TEXTO
        if "image" not in data:
            payload = {
                "model": TEXT_MODEL,
                "messages": [
                    {"role": "user", "content": data.get("message", "")}
                ]
            }

        # ✅ TEXTO + IMAGEN
        else:
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

        r = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload
        )

        raw = r.json()

        # ✅ SI HAY ERROR DE GROQ → lo devolvemos
        if "error" in raw:
            return jsonify({
                "reply": f"ERROR GROQ: {raw['error']}",
                "raw": raw
            })

        # ✅ EXTRAER RESPUESTA
        try:
            content = raw["choices"][0]["message"]["content"]
            if isinstance(content, list):
                for item in content:
                    if item.get("type") == "output_text":
                        return jsonify({"reply": item["text"], "raw": raw})
                return jsonify({"reply": "No hay texto en la salida", "raw": raw})
            else:
                return jsonify({"reply": content, "raw": raw})

        except Exception as e:
            return jsonify({"reply": f"ERROR EXTRACTION: {str(e)}", "raw": raw})

    except Exception as e:
        return jsonify({"reply": f"SERVER ERROR: {str(e)}"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
