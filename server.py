from flask import Flask, request, jsonify
from groq import Groq
import os

app = Flask(__name__)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()

    if not data or "messages" not in data:
        return jsonify({"error": "No messages provided"}), 400

    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=data["messages"]
        )
        reply = response.choices[0].message.content
        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/", methods=["GET"])
def home():
    return "Backend funcionando ✅", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
