from flask import Flask, request, jsonify
import psycopg2
import psycopg2.extras
import base64
import json

app = Flask(__name__)

# ✅ CONEXIÓN A POSTGRES (Render)
DB_URL = "postgresql://mi_base_de_datos_7ap6_user:6bOxgNN8k3NJf1ZNJCMT8yebHbWdI4PC@dpg-d49ioivgi27c73ccefq0-a.oregon-postgres.render.com/mi_base_de_datos_7ap6"

conn = psycopg2.connect(DB_URL)
cur = conn.cursor()

# ✅ Crear tabla si no existe
cur.execute("""
CREATE TABLE IF NOT EXISTS mensajes (
    id SERIAL PRIMARY KEY,
    rol TEXT NOT NULL,
    contenido TEXT,
    imagen TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
)
""")
conn.commit()


# ✅ Guardar mensaje
def guardar_mensaje(rol, contenido, imagen=None):
    cur.execute(
        "INSERT INTO mensajes (rol, contenido, imagen) VALUES (%s, %s, %s)",
        (rol, contenido, imagen)
    )
    conn.commit()


# ✅ Cargar historial completo
def cargar_historial():
    cur.execute("SELECT rol, contenido, imagen FROM mensajes ORDER BY id ASC")
    rows = cur.fetchall()

    historial = []
    for r in rows:
        if r[2]:  # imagen
            historial.append({
                "role": r[0],
                "image": r[2]
            })
        else:
            historial.append({
                "role": r[0],
                "content": r[1]
            })
    return historial


# ✅ Gemini analiza imagen
def gemini_describe_image(base64_img, prompt):
    return f"[Análisis falso de Gemini para pruebas: {prompt}]"


# ✅ Groq responde
def groq_chat(messages):
    texto = "\n".join([m.get("content", "") for m in messages])
    return "Groq respondió según historial:\n\n" + texto


# ✅ RUTA PRINCIPAL /chat
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()

    base64_img = data.get("image")
    user_text = data.get("message", "")

    # ✅ Cargar historial desde BD
    history = cargar_historial()

    groq_messages = []

    # ✅ Convertir HISTORIAL para Groq
    for h in history:

        if "content" in h and h["content"]:
            groq_messages.append({
                "role": h["role"],
                "content": h["content"]
            })

        elif "image" in h and h["image"]:
            gemini_analysis = gemini_describe_image(
                h["image"],
                "Describe esta imagen de manera detallada."
            )

            groq_messages.append({
                "role": h["role"],
                "content": f"[Imagen anterior analizada por Gemini]:\n\n{gemini_analysis}"
            })

    # ✅ Si viene imagen nueva
    if base64_img:
        gemini_analysis = gemini_describe_image(
            base64_img,
            user_text if user_text else "Analiza la imagen enviada."
        )

        groq_messages.append({
            "role": "user",
            "content": f"El usuario envió una nueva imagen:\n\n{gemini_analysis}"
        })

        # ✅ GUARDAR mensaje en BD
        guardar_mensaje("user", None, base64_img)
        guardar_mensaje("system", gemini_analysis)

        final = groq_chat(groq_messages)

        guardar_mensaje("assistant", final)

        return jsonify({"reply": final})

    # ✅ Si viene solo texto
    groq_messages.append({
        "role": "user",
        "content": user_text
    })

    guardar_mensaje("user", user_text)

    final = groq_chat(groq_messages)

    guardar_mensaje("assistant", final)

    return jsonify({"reply": final})


@app.route("/")
def home():
    return "Servidor con historial persistente ✅"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
