from flask import Flask, request, jsonify
import requests
import os
import json # Necesario para procesar la respuesta de Gemini

app = Flask(__name__)

# --- CONFIGURACIÓN DE APIS ---
# Groq (Solo para texto, por su velocidad)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_TEXT_MODEL = "llama-3.1-8b-instant"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Gemini (Para multimodalidad, ya que Groq Vision no está disponible)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") # Asegúrate de definir esta variable de entorno
GEMINI_VISION_MODEL = "gemini-2.5-flash"
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_VISION_MODEL}:generateContent"
)
# ------------------------------

def extract_groq_reply(data):
    """Extrae la respuesta de un payload de Groq/OpenAI."""
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        # Si la API devuelve un error (ej. 400), r.json() contiene el mensaje de error
        return f"Error en la API de Groq: {data.get('error', {}).get('message', 'Formato de respuesta desconocido.')}"

def extract_gemini_reply(data):
    """Extrae la respuesta de un payload de Gemini."""
    try:
        # La respuesta de Gemini usa un formato diferente
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        # Manejo de error para Gemini
        return f"Error en la API de Gemini. Mensaje: {data.get('error', {}).get('message', 'Formato de respuesta desconocido.')}"


@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Servidor activo ✅ (Groq + Gemini Multimodal)"})


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    base64_image = data.get("image")
    prompt_text = data.get("message", "Describe esta imagen.")

    # 1. Caso Multimodal (TEXTO + IMAGEN)
    if base64_image:
        if not GEMINI_API_KEY:
            return jsonify({"reply": "Error: La clave GEMINI_API_KEY no está configurada para el modo multimodal."}), 500

        # El payload de Gemini es diferente, usa "contents" y el formato inlineData
        gemini_payload = {
            "contents": [
                {
                    "parts": [
                        # El texto del prompt
                        {"text": prompt_text},
                        # La imagen codificada en Base64
                        {
                            "inlineData": {
                                "mimeType": "image/jpeg", # Asumimos JPEG, puedes mejorar esto
                                "data": base64_image,
                            }
                        }
                    ]
                }
            ],
            # Opcional: configurar generación (ej. para forzar solo texto)
            "config": {
                "responseMimeType": "text/plain" 
            }
        }
        
        try:
            r = requests.post(
                f"{GEMINI_URL}?key={GEMINI_API_KEY}",
                headers={"Content-Type": "application/json"},
                json=gemini_payload
            )
            
            # Verificar si la solicitud fue exitosa antes de extraer el contenido
            if r.status_code != 200:
                 # Manejo de error específico de la API
                error_data = r.json()
                error_message = error_data.get("error", {}).get("message", "Error desconocido al llamar a Gemini.")
                return jsonify({"reply": f"Error de API Gemini ({r.status_code}): {error_message}"}), r.status_code


            reply = extract_gemini_reply(r.json())
            return jsonify({"reply": reply})

        except requests.exceptions.RequestException as e:
            return jsonify({"reply": f"Error de conexión con Gemini: {str(e)}"})

    # 2. Caso Solo Texto (Usamos Groq por su velocidad)
    else:
        if not GROQ_API_KEY:
             return jsonify({"reply": "Error: La clave GROQ_API_KEY no está configurada para el modo solo texto."}), 500
             
        groq_payload = {
            "model": GROQ_TEXT_MODEL,
            "messages": [
                {"role": "user", "content": prompt_text}
            ]
        }
        
        try:
            r = requests.post(
                GROQ_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=groq_payload
            )
            
            # Si Groq devuelve un error (ej. 401 Unauthorized), capturarlo
            if r.status_code != 200:
                error_data = r.json()
                error_message = error_data.get("error", {}).get("message", "Error desconocido al llamar a Groq.")
                return jsonify({"reply": f"Error de API Groq ({r.status_code}): {error_message}"}), r.status_code


            reply = extract_groq_reply(r.json())
            return jsonify({"reply": reply})
            
        except requests.exceptions.RequestException as e:
            return jsonify({"reply": f"Error de conexión con Groq: {str(e)}"})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
